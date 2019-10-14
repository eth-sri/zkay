from typing import Dict, Optional, List

from compiler.privacy.circuit_generation.circuit_generator import HybridArgumentIdf, CircuitHelper, EncParamIdf
from compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from compiler.privacy.used_contract import UsedContract
from zkay_ast.ast import ReclassifyExpr, Expression, ConstructorOrFunctionDefinition, AssignmentStatement, IfStatement, \
    BuiltinFunction, FunctionCallExpr, IdentifierExpr, Parameter, VariableDeclaration, \
    AnnotatedTypeName, StateVariableDeclaration, Mapping, MeExpr, MemberAccessExpr, Identifier, \
    VariableDeclarationStatement, Statement, Block, ExpressionStatement, \
    ConstructorDefinition, UserDefinedTypeName, SourceUnit, ReturnStatement, LocationExpr

pki_contract_name = 'pki'
proof_param_name = '__proof'
verification_function_name = 'check_verify'
default_return_var_name = '__return_value'
contract_var_suffix = 'inst'


class DecryptionExpr(Expression):
    def __init__(self, loc: LocationExpr):
        super().__init__()
        self.loc = loc
        self.annotated_type = loc.annotated_type

    def get_rnd(self) -> HybridArgumentIdf:
        pass


class ZkayTransformer(AstTransformerVisitor):
    def __init__(self):
        super().__init__()
        self.circuit_generators: Dict[ConstructorOrFunctionDefinition, CircuitHelper] = {}
        self.current_generator: Optional[CircuitHelper] = None
        self.current_verifier: Optional[Identifier] = None
        self.used_contracts: List[UsedContract] = []
        self.return_var: Optional[Identifier] = None

    # --------------------------
    # Transform annotated types
    # --------------------------

    @staticmethod
    def get_real_type(t: AnnotatedTypeName):
        return AnnotatedTypeName.cipher_type() if t.is_private() else AnnotatedTypeName(t.type_name, None)

    def visitVariableDeclaration(self, ast: VariableDeclaration):
        return ast.replaced_with(VariableDeclaration(
            [k for k in ast.keywords if k != 'final'],
            self.get_real_type(ast.annotated_type),
            ast.idf
        ))

    def visitStateVariableDeclaration(self, ast: StateVariableDeclaration):
        return ast.replaced_with(StateVariableDeclaration(
            self.get_real_type(ast.annotated_type),
            [k for k in ast.keywords if k != 'final'],
            ast.idf,
            self.visit(ast.expr)
        ))

    def visitMapping(self, ast: Mapping):
        return ast.replaced_with(Mapping(
            ast.key_type,
            None,
            self.get_real_type(ast.value_type)
        ))

    @staticmethod
    def visitMeExpr(ast: MeExpr):
        return ast.replaced_with(MemberAccessExpr(IdentifierExpr(Identifier('msg')), Identifier('sender')))

    # --------------------------
    # Transform functions
    # --------------------------

    @staticmethod
    def import_contract(ast: SourceUnit, vname: str) -> (UsedContract, StateVariableDeclaration):
        inst_idf = Identifier(f'{vname}_{contract_var_suffix}')
        c_type = AnnotatedTypeName(UserDefinedTypeName([Identifier(vname)]), None)
        uc = UsedContract(f'{vname}.sol', c_type, inst_idf)
        sv = StateVariableDeclaration(c_type, [], inst_idf, None)
        ast.used_contracts.append(uc.filename)
        return uc, sv

    def visitSourceUnit(self, ast: SourceUnit):
        # Include pki contract
        pki_uc, pki_sv = self.import_contract(ast, pki_contract_name)

        for c in ast.contracts:
            # Transform types of normal state variables
            c.state_variable_declarations = list(map(self.visit, c.state_variable_declarations))

            # Ref pki contract
            self.used_contracts = [pki_uc]
            c.state_variable_declarations.append(pki_sv)

            # Ref all verification contracts
            for idx, f in enumerate(c.function_definitions + c.constructor_definitions):
                uc, sv = self.import_contract(ast, f'Verify_{c.idf.name}_${idx}_{f.name}')
                self.used_contracts.append(uc)
                c.state_variable_declarations.append(sv)

            # Visit functions and constructors
            ucs = self.used_contracts[1:]
            for idx, f in enumerate(c.function_definitions):
                self.current_verifier = ucs[idx]
                c.function_definitions[idx] = self.visit(f)

            ucs = ucs[len(c.function_definitions):]
            for idx, constr in enumerate(c.constructor_definitions):
                self.current_verifier = ucs[idx]
                c.constructor_definitions[idx] = self.visit(constr)

        return ast

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        circuit_generator = CircuitHelper(self)
        self.circuit_generators[ast] = circuit_generator
        self.current_generator = circuit_generator
        self.visit_children(ast)

        for p in ast.parameters:
            """ Rule (8) """
            if p.annotated_type.is_private():
                self.current_generator.ensure_encryption(EncParamIdf(p.idf.name), Expression.me_expr(), HybridArgumentIdf(p.idf.name))

        # Add external contract initialization for constructor
        c_assignments: List[Statement] = []
        if isinstance(ast, ConstructorDefinition):
            for c in self.used_contracts:
                pidf = Identifier(f'{c.state_variable_idf.name}_')
                ast.parameters.append(Parameter([], c.contract_type, pidf, None))
                c_assignments.append(AssignmentStatement(
                    lhs=IdentifierExpr(c.state_variable_idf), rhs=IdentifierExpr(pidf))
                )

        # Add additional parameters
        ast.parameters += self.current_generator.additional_params
        ast.parameters += Parameter([], AnnotatedTypeName.proof_type(), Identifier(proof_param_name), None)

        # Prepend public key requests (and external contract assignments for constructor)
        ast.body.statements = c_assignments + list(self.current_generator.pk_for_label.values()) + ast.body.statements

        # Add call into verification contract at the end
        verify = ExpressionStatement(FunctionCallExpr(
            MemberAccessExpr(IdentifierExpr(self.current_verifier), Identifier(verification_function_name)),
            [IdentifierExpr(arg) for arg in self.current_generator.p]
        ))
        ast.body.statements.append(verify)

        # Make sure return happens after verify
        if self.return_var is not None:
            ast.body.statements.append(ReturnStatement(IdentifierExpr(self.return_var)))
            self.return_var = None

        return ast

    # --------------------------
    # Transform statements
    # --------------------------

    def visitReturnStatement(self, ast: ReturnStatement):
        if ast.expr is None:
            return None

        e = self.visit(ast.expr)
        rv = e.idf if isinstance(e, IdentifierExpr) else Identifier(default_return_var_name)
        self.return_var = rv
        return ast.replaced_with(VariableDeclarationStatement(VariableDeclaration([], ast.expr.annotated_type, rv), e))

    def visitBlock(self, ast: Block):
        self.visit_children(ast)

        new_stmts = []
        tv = self.current_generator.temp_vars
        for stmt in ast.statements:
            if stmt in tv:
                new_stmts += tv[stmt]
            new_stmts.append(stmt)
        ast.statements = new_stmts
        return ast

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        """ Rule (2) """
        return ast.replaced_with(AssignmentStatement(
            lhs=ZkayExpressionTransformer(self).visit(ast.lhs),
            rhs=ZkayExpressionTransformer(self).visit(ast.rhs)
        ))

    def visitIfStatement(self, ast: IfStatement):
        """ Rule (6) """
        # TODO guard condition
        return ast.replaced_with(IfStatement(
            condition=ZkayExpressionTransformer(self).visit(ast.condition),
            then_branch=self.visit(ast.then_branch),
            else_branch=self.visit(ast.else_branch)
        ))

    def visitExpression(self, ast: Expression):
        return ast.replaced_with(ZkayExpressionTransformer(self).visit(ast))


class ZkayExpressionTransformer(AstTransformerVisitor):
    def __init__(self, t: ZkayTransformer):
        super().__init__()
        self.move_out = t.current_generator.move_out

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        """ Rule (9) """
        if isinstance(ast.func, BuiltinFunction) and ast.func.is_index():
            return ast.replaced_with(FunctionCallExpr(
                ast.func,
                [self.visit(ast.args[0]), self.visit(ast.args[1])]
            ))
        else:
            return self.visitExpression(ast)

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        """ Rule (11) """
        return self.move_out(ast.expr, ast.expr.annotated_type.privacy_annotation)

    def visitExpression(self, ast: Expression):
        """ Rule (12) """
        if ast.annotated_type.is_private():
            return self.move_out(ast, Expression.me_expr())
        else:
            return super().visit(ast)


class ZkayCircuitTransformer(AstTransformerVisitor):
    def __init__(self, t: ZkayTransformer):
        super().__init__()
        self.move_in = t.current_generator.move_in

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction) and ast.func.is_index():
            return self.transform_location(ast)
        else:
            self.visit_children(ast)
            return ast

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        return self.transform_location(ast)

    def transform_location(self, loc: LocationExpr):
        """ Rule (14) """
        return self.move_in(loc, Expression.me_expr() if loc.annotated_type.is_private() else Expression.all_expr())

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        """ Rule (15) """
        return self.visit(ast.expr)
