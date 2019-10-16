from typing import Dict, Optional, List, Tuple

from compiler.privacy.circuit_generation.circuit_helper import HybridArgumentIdf, CircuitHelper, EncParamIdf
from compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from compiler.privacy.used_contract import UsedContract
from zkay_ast.ast import ReclassifyExpr, Expression, ConstructorOrFunctionDefinition, AssignmentStatement, IfStatement, \
    BuiltinFunction, FunctionCallExpr, IdentifierExpr, Parameter, VariableDeclaration, \
    AnnotatedTypeName, StateVariableDeclaration, Mapping, MeExpr, MemberAccessExpr, Identifier, \
    VariableDeclarationStatement, Block, ExpressionStatement, \
    ConstructorDefinition, UserDefinedTypeName, SourceUnit, ReturnStatement, LocationExpr, TypeName, AST, \
    Comment, LiteralExpr, Statement, SimpleStatement, FunctionDefinition

pki_contract_name = 'PublicKeyInfrastructure'
proof_param_name = '__proof'
verification_function_name = 'check_verify'
default_return_var_name = '__return_value'
contract_var_suffix = 'inst'


def transform_ast(ast: AST) -> Tuple[AST, 'ZkayTransformer']:
    zt = ZkayTransformer()
    new_ast = zt.visit(ast)
    return new_ast, zt


class ZkayTransformer(AstTransformerVisitor):
    """ Transformer, which transforms zkay contracts into equivalent public solidity contracts """

    def __init__(self):
        super().__init__()
        self.circuit_generators: Dict[ConstructorOrFunctionDefinition, CircuitHelper] = {}
        self.current_generator: Optional[CircuitHelper] = None
        self.used_contracts: List[UsedContract] = []
        self.var_decl_trafo = ZkayVarDeclTransformer()

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
            # Ref pki contract
            self.used_contracts = [pki_uc]
            ext_var_decls = [pki_sv]

            # Transform types of normal state variables
            c.state_variable_declarations = list(filter(None.__ne__, map(self.var_decl_trafo.visit, c.state_variable_declarations)))

            # Transform function children and include required verification contracts
            for f in c.constructor_definitions + c.function_definitions:
                self.transform_function_children(f)
                if self.current_generator.requires_verification():
                    uc, sv = self.import_contract(ast, f'Verify_{c.idf.name}_{len(ext_var_decls)-1}_{f.name}')
                    self.current_generator.verifier_contract = uc
                    self.used_contracts.append(uc)
                    ext_var_decls.append(sv)

            # Add external contract state variables
            c.state_variable_declarations = Comment.comment_list('External contracts', ext_var_decls) + \
                                            [Comment('User state variables')] + c.state_variable_declarations

            # Transform function definitions
            for f in c.constructor_definitions + c.function_definitions:
                self.transform_function_definition(f)

        return ast

    def transform_function_children(self, ast: ConstructorOrFunctionDefinition):
        circuit_generator = CircuitHelper(self.used_contracts, ZkayExpressionTransformer)
        self.circuit_generators[ast] = circuit_generator
        self.current_generator = circuit_generator

        # Check encryption for all private args
        for p in ast.parameters:
            """ * of T_e rule 8 """
            if p.annotated_type.is_private():
                circuit_generator.ensure_encryption(EncParamIdf(p.idf.name, p.annotated_type.type_name),
                                                    Expression.me_expr(),
                                                    HybridArgumentIdf(p.idf.name, None, TypeName.cipher_type()))

        # Transform parameters
        ast.parameters = list(map(self.var_decl_trafo.visit, ast.parameters))
        if isinstance(ast, FunctionDefinition):
            ast.return_parameters = list(map(self.var_decl_trafo.visit, ast.return_parameters))

        # Transform body
        ast.body = ZkayStatementTransformer(circuit_generator).visit(ast.body)
        return ast

    def transform_function_definition(self, ast: ConstructorOrFunctionDefinition):
        circuit_generator = self.circuit_generators[ast]
        verifier = circuit_generator.verifier_contract
        requires_proof = verifier is not None

        preamble: List[AST] = []

        # Add external contract initialization for constructor
        if isinstance(ast, ConstructorDefinition):
            c_assignments = []
            for c in self.used_contracts:
                pidf = Identifier(f'{c.state_variable_idf.name}_')
                ast.parameters.append(Parameter([], c.contract_type, pidf, None))
                c_assignments.append(AssignmentStatement(
                    lhs=IdentifierExpr(c.state_variable_idf), rhs=IdentifierExpr(pidf))
                )
            preamble += Comment.comment_list('Assigning contract instance variables', c_assignments)

        if not requires_proof:
            if ast.body.statements and isinstance(ast.body.statements[-1], Comment):
                # Remove superfluous empty line
                ast.body.statements.pop()
            ast.body.statements = preamble + ast.body.statements
        else:
            # Declare array with temporary variables
            if circuit_generator.temp_name_factory.count > 0:
                preamble += Comment.comment_list('Declare array to store public circuit inputs', [
                    VariableDeclarationStatement(VariableDeclaration(
                        [], AnnotatedTypeName.array_all(
                            AnnotatedTypeName.uint_all(), circuit_generator.temp_name_factory.count
                        ), Identifier(circuit_generator.temp_name_factory.base_name), 'memory'
                    ), None)
                ])

            # Add new parameters with circuit out values
            if circuit_generator.param_name_factory.count > 0:
                ast.parameters.append(Parameter([],
                                                AnnotatedTypeName.array_all(AnnotatedTypeName.uint_all(),
                                                                            circuit_generator.param_name_factory.count),
                                                Identifier(circuit_generator.param_name_factory.base_name), 'memory'))

            # Add proof parameter
            ast.parameters.append(Parameter([], AnnotatedTypeName.proof_type(), Identifier(proof_param_name), 'memory'))

            # Prepend public key requests (and external contract assignments for constructor)
            ast.body.statements = preamble + \
                                  Comment.comment_list('Request required public keys',
                                                       list(circuit_generator.pk_for_label.values())) + \
                                  ast.body.statements

            # Add call to verifier
            verify = ExpressionStatement(FunctionCallExpr(
                MemberAccessExpr(IdentifierExpr(verifier.state_variable_idf), Identifier(verification_function_name)), [
                    IdentifierExpr(Identifier(proof_param_name)),
                    IdentifierExpr(Identifier(circuit_generator.temp_name_factory.base_name)),
                    IdentifierExpr(Identifier(circuit_generator.param_name_factory.base_name))
                ]
            ))
            ast.body.statements += [Comment('Verify zk proof of execution'), verify]

        # Add return statement at the end if necessary (was previously replaced by assignment to return_var by ZkayStatementTransformer)
        if circuit_generator.return_var is not None:
            ast.body.statements.append(ReturnStatement(IdentifierExpr(circuit_generator.return_var)))


class ZkayVarDeclTransformer(AstTransformerVisitor):
    """ Transformer for types, which was left out in the paper """

    def __init__(self):
        super().__init__()
        self.expr_trafo = ZkayExpressionTransformer(None)

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
        return AnnotatedTypeName.cipher_type() if ast.is_private() else AnnotatedTypeName(self.visit(ast.type_name), None)

    def visitVariableDeclaration(self, ast: VariableDeclaration):
        ast.keywords = [k for k in ast.keywords if k != 'final']
        return self.visit_children(ast)

    def visitParameter(self, ast: Parameter):
        return self.visit_children(ast)

    def visitStateVariableDeclaration(self, ast: StateVariableDeclaration):
        if ast.annotated_type.type_name.code().startswith('<'):
            return None

        ast.keywords = [k for k in ast.keywords if k != 'final']
        ast.expr = self.expr_trafo.visit(ast.expr)
        return self.visit_children(ast)

    def visitMapping(self, ast: Mapping):
        ast.key_label = None
        return self.visit_children(ast)


class ZkayStatementTransformer(AstTransformerVisitor):
    """ Corresponds to T from paper, (with additional handling of return statement) """

    def __init__(self, current_gen: CircuitHelper):
        super().__init__()
        self.gen = current_gen
        self.expr_trafo = ZkayExpressionTransformer(self.gen)
        self.var_decl_trafo = ZkayVarDeclTransformer()

    def visitReturnStatement(self, ast: ReturnStatement):
        if ast.expr is None:
            return None

        e = self.expr_trafo.visit(ast.expr)
        rv = e.idf if isinstance(e, IdentifierExpr) else Identifier(default_return_var_name)
        assert self.gen.return_var is None
        self.gen.return_var = rv

        storage_loc = None if ast.expr.annotated_type.type_name.is_primitive_type() else 'memory'
        repl = ast.replaced_with(VariableDeclarationStatement(VariableDeclaration([], ast.expr.annotated_type, rv, storage_loc), e))
        if ast in self.gen.old_code_and_temp_var_decls_for_stmt:
            self.gen.old_code_and_temp_var_decls_for_stmt[repl] = self.gen.old_code_and_temp_var_decls_for_stmt[ast]
            del self.gen.old_code_and_temp_var_decls_for_stmt[ast]
        return repl

    def visitBlock(self, ast: Block):
        """ Rule (1) """
        self.visit_children(ast)

        block_stmts = []
        tv = self.gen.old_code_and_temp_var_decls_for_stmt
        last = True
        for stmt in ast.statements:
            if stmt in tv:
                if not last:
                    block_stmts.append(Comment())

                last = True
                old_code, new_stmts = tv[stmt]
                block_stmts += Comment.comment_wrap_block(old_code, new_stmts + [stmt])
            else:
                last = False
                block_stmts.append(stmt)
        ast.statements = block_stmts + ([Comment()] if not last else [])
        return ast

    def process_statement_child(self, child: AST):
        if isinstance(child, Expression):
            return self.expr_trafo.visit(child)
        else:
            assert isinstance(child, VariableDeclaration), f'Child had unhandled type {type(child)}'
            return self.var_decl_trafo.visit(child)

    def visitStatement(self, ast: Statement):
        """ Rules (2), (3), (4) """
        assert isinstance(ast, SimpleStatement) or isinstance(ast, VariableDeclarationStatement)
        ast.process_children(self.process_statement_child)
        return ast

    def visitIfStatement(self, ast: IfStatement):
        """ Rule (6) """
        # TODO guard condition
        ast.condition = self.expr_trafo.visit(ast.condition)
        ast.then_branch = self.visit(ast.then_branch)
        ast.else_branch = self.visit(ast.else_branch)
        return ast

    def visitExpression(self, ast: Expression):
        assert False, f"Missed an expression of type {type(ast)}"


class ZkayExpressionTransformer(AstTransformerVisitor):
    """ Corresponds to T_L / T_e from paper (parameter encryption checks are handled outside of this) """

    def __init__(self, current_generator: Optional[CircuitHelper]):
        super().__init__()
        self.gen = current_generator

    @staticmethod
    def visitMeExpr(ast: MeExpr):
        return ast.replaced_with(MemberAccessExpr(IdentifierExpr(Identifier('msg')), Identifier('sender')))

    def visitLiteralExpr(self, ast: LiteralExpr):
        """ Rule (7) """
        return ast

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        """ Rule (8) """
        return ast

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
        return self.gen.move_out(ast.expr, ast.privacy)

    def visitExpression(self, ast: Expression):
        """ Rule (10 & 12) """
        if ast.annotated_type is not None and ast.annotated_type.is_private():
            return self.gen.move_out(ast, Expression.me_expr())
        else:
            return self.visit_children(ast)


class ZkayCircuitTransformer(AstTransformerVisitor):
    """ Corresponds to T_phi from paper """

    def __init__(self, current_generator: CircuitHelper):
        super().__init__()
        self.gen = current_generator

    def visitLiteralExpr(self, ast: LiteralExpr):
        """ Rule (13) """
        return ast

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction) and ast.func.is_index():
            return self.transform_location(ast)
        else:
            return self.visit_children(ast)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        return self.transform_location(ast)

    def transform_location(self, loc: LocationExpr):
        """ Rule (14) """
        return self.gen.move_in(loc, Expression.me_expr() if loc.annotated_type.is_private() else Expression.all_expr())

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        """ Rule (15) """
        return self.visit(ast.expr)

    def visitExpression(self, ast: Expression):
        """ Rule (16) """
        return self.visit_children(ast)
