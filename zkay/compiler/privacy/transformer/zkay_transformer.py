import re
from typing import Dict, Optional, List, Tuple

import zkay.config as cfg

from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.compiler.privacy.circuit_generation.circuit_helper import HybridArgumentIdf, CircuitHelper, EncParamIdf
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.solidity.fake_solidity_compiler import WS_PATTERN, ID_PATTERN
from zkay.zkay_ast.ast import ReclassifyExpr, Expression, ConstructorOrFunctionDefinition, AssignmentStatement, \
    IfStatement, FunctionCallExpr, IdentifierExpr, Parameter, VariableDeclaration, \
    AnnotatedTypeName, StateVariableDeclaration, Mapping, MeExpr, MemberAccessExpr, Identifier, \
    VariableDeclarationStatement, Block, ExpressionStatement, \
    UserDefinedTypeName, SourceUnit, ReturnStatement, LocationExpr, TypeName, AST, \
    Comment, LiteralExpr, Statement, SimpleStatement, FunctionDefinition, IndentBlock, IndexExpr, NumberLiteralExpr, CastExpr
from zkay.zkay_ast.pointers.parent_setter import set_parents
from zkay.zkay_ast.pointers.symbol_table import link_identifiers

proof_param_name = 'proof__'
verification_function_name = 'check_verify'
default_return_var_name = 'return_value__'


def transform_ast(ast: AST) -> Tuple[AST, 'ZkayTransformer']:
    zt = ZkayTransformer()
    new_ast = zt.visit(ast)

    # restore all parent pointers and identifier targets
    set_parents(new_ast)
    link_identifiers(new_ast)
    return new_ast, zt


class ZkayTransformer(AstTransformerVisitor):
    """ Transformer, which transforms zkay contracts into equivalent public solidity contracts """

    def __init__(self):
        super().__init__()
        self.circuit_generators: Dict[ConstructorOrFunctionDefinition, CircuitHelper] = {}
        self.current_generator: Optional[CircuitHelper] = None
        self.var_decl_trafo = ZkayVarDeclTransformer()

    def import_contract(self, ast: SourceUnit, vname: str) -> StateVariableDeclaration:
        inst_idf = get_contract_instance_idf(vname)
        c_type = UserDefinedTypeName([Identifier(vname)])
        fname = f'./{vname}.sol'

        if self.current_generator:
            self.current_generator.verifier_contract_type = c_type
            self.current_generator.verifier_contract_filename = fname
        ast.used_contracts.append(fname)

        return StateVariableDeclaration(AnnotatedTypeName(c_type, None), ['constant'], inst_idf.clone(), CastExpr(c_type, NumberLiteralExpr(0)))

    def visitSourceUnit(self, ast: SourceUnit):
        # Include pki contract
        pki_sv = self.import_contract(ast, cfg.pki_contract_name)

        for c in ast.contracts:
            # Ref pki contract
            ext_var_decls = [pki_sv]

            # Transform types of normal state variables
            c.state_variable_declarations = list(filter(None.__ne__, map(self.var_decl_trafo.visit, c.state_variable_declarations)))

            # Transform function children and include required verification contracts
            for f in c.constructor_definitions + c.function_definitions:
                self.transform_function_children(f)
                if self.current_generator.requires_verification():
                    contract_state_var_decl = self.import_contract(ast, f'Verify_{c.idf.name}_{len(ext_var_decls) - 1}_{f.name}')
                    ext_var_decls.append(contract_state_var_decl)

            # Add external contract state variables
            c.state_variable_declarations = Comment.comment_list('External contracts', ext_var_decls) + \
                                            [Comment('User state variables')] + c.state_variable_declarations

            # TODO add zk_data struct declaration for this function

            # Transform function definitions
            for f in c.constructor_definitions + c.function_definitions:
                self.transform_function_definition(f)

        return ast

    def transform_function_children(self, ast: ConstructorOrFunctionDefinition):
        circuit_generator = CircuitHelper(ast, ZkayExpressionTransformer, ZkayCircuitTransformer)
        self.circuit_generators[ast] = circuit_generator
        self.current_generator = circuit_generator

        # Check encryption for all private args
        for p in ast.parameters:
            """ * of T_e rule 8 """
            if p.annotated_type.is_private():
                circuit_generator.encrypt_parameter(p)

        # Transform parameters
        ast.parameters = list(map(self.var_decl_trafo.visit, ast.parameters))
        if isinstance(ast, FunctionDefinition):
            ast.return_parameters = list(map(self.var_decl_trafo.visit, ast.return_parameters))

        # Transform body
        ast.body = ZkayStatementTransformer(circuit_generator).visit(ast.body)
        return ast

    def transform_function_definition(self, ast: ConstructorOrFunctionDefinition):
        circuit_generator = self.circuit_generators[ast]

        preamble: List[AST] = []
        # Declare return variable if necessary
        if isinstance(ast, FunctionDefinition) and ast.return_parameters:
            assert len(ast.return_parameters) == 1  # for now
            preamble += Comment.comment_list("Declare return variable", [
                VariableDeclarationStatement(VariableDeclaration(
                    [], ast.return_parameters[0].annotated_type, Identifier(default_return_var_name)
                ), None)
            ])

        if not circuit_generator.requires_verification():
            #if ast.body.statements and isinstance(ast.body.statements[-1], Comment):
                # Remove superfluous empty line
             #   ast.body.statements.pop()
            ast.body.statements = preamble + ast.body.statements
        else:
            # TODO initialize zk_data struct (deserialize out_ array into it)

            # Declare array with temporary variables
            if circuit_generator._in_name_factory.count > 0:
                preamble += Comment.comment_list('Declare array to store public circuit inputs', [
                    VariableDeclarationStatement(VariableDeclaration(
                        [], AnnotatedTypeName.array_all(
                            AnnotatedTypeName.uint_all(), circuit_generator._in_name_factory.count
                        ), Identifier(circuit_generator._in_name_factory.base_name), 'memory'
                    ), None)
                ])

            # Add new parameters with circuit out values
            if circuit_generator.has_out_args:
                out_name, out_count = circuit_generator.public_out_array
                ast.parameters.append(Parameter([],
                                                AnnotatedTypeName.array_all(AnnotatedTypeName.uint_all(), out_count),
                                                Identifier(out_name), 'memory'))

            # Add proof parameter
            ast.parameters.append(Parameter([], AnnotatedTypeName.proof_type(), Identifier(proof_param_name), 'memory'))

            # TODO deserialize zk_data into in_ array
            offset = 0
            for s in circuit_generator.input_idfs:
                if s.t.size_in_uints == 1:
                    AssignmentStatement(IndexExpr(IdentifierExpr(Identifier(cfg.zk_in_name)), NumberLiteralExpr(offset)),
                                        s.get_loc_expr().implicitly_converted(AnnotatedTypeName.uint_all()))
                else:
                    # TODO
                    pass

            # Call to verifier
            verifier = IdentifierExpr(get_contract_instance_idf(circuit_generator.verifier_contract_type.code()))
            verifier_args = [IdentifierExpr(Identifier(proof_param_name))]
            verifier_args += [IdentifierExpr(Identifier(name)) for name, _ in circuit_generator.public_arg_arrays]
            verify = ExpressionStatement(FunctionCallExpr(MemberAccessExpr(verifier, Identifier(verification_function_name)), verifier_args))

            # Assemble new body (public key requests, transformed statements, verification invocation)
            ast.body.statements = preamble + \
                                  Comment.comment_wrap_block('Backup private arguments for verification',
                                                             circuit_generator.param_to_in_assignments) + \
                                  [IndentBlock("BODY", ast.body.statements)] + \
                                  Comment.comment_wrap_block('Request required public keys',
                                                             circuit_generator.public_key_requests) + \
                                  [Comment('Verify zk proof of execution'), verify]

        # Add return statement at the end if necessary (was previously replaced by assignment to return_var by ZkayStatementTransformer)
        if circuit_generator.return_var is not None:
            ast.body.statements.append(ReturnStatement(IdentifierExpr(circuit_generator.return_var.clone())))


class ZkayVarDeclTransformer(AstTransformerVisitor):
    """ Transformer for types, which was left out in the paper """

    def __init__(self):
        super().__init__()
        self.expr_trafo = ZkayExpressionTransformer(None)

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
        new_t = AnnotatedTypeName.cipher_type() if ast.is_private() else AnnotatedTypeName(self.visit(ast.type_name.clone()), None)
        if ast.is_private():
            new_t.old_priv_text = f'{ast.code()}' if ast.type_name != new_t.type_name else f'@{ast.privacy_annotation.code()}'
        return new_t

    def visitVariableDeclaration(self, ast: VariableDeclaration):
        ast.keywords = [k for k in ast.keywords if k != 'final']
        return self.visit_children(ast)

    def visitParameter(self, ast: Parameter):
        ast.original_type = ast.annotated_type
        return self.visit_children(ast)

    def visitStateVariableDeclaration(self, ast: StateVariableDeclaration):
        ast.keywords = [k for k in ast.keywords if k != 'final' and k != 'public']
        ast.keywords.append('public')  # make sure every state var gets a public getter (TODO maybe there is another solution)
        ast.expr = self.expr_trafo.visit(ast.expr)
        return self.visit_children(ast)

    def visitMapping(self, ast: Mapping):
        if ast.key_label is not None:
            ast.key_label = ast.key_label.name
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
        assert self.gen.return_var is None

        rv = Identifier(default_return_var_name)
        self.gen.return_var = rv
        return ast.replaced_with(AssignmentStatement(IdentifierExpr(rv), self.expr_trafo.visit(ast.expr)))

    def visitBlock(self, ast: Block):
        """ Rule (1) """
        new_statements = []
        first = True
        for idx, stmt in enumerate(ast.statements):
            old_code = stmt.code()
            transformed_stmt = self.visit(stmt)
            if transformed_stmt is None:
                continue

            old_code_wo_annotations = re.sub(r'(?=\b)me(?=\b)', 'msg.sender',
                                             re.sub(f'@{WS_PATTERN}*{ID_PATTERN}', '', old_code))
            new_code_wo_annotation_comments = re.sub(r'/\*.*?\*/', '', transformed_stmt.code())
            if old_code_wo_annotations == new_code_wo_annotation_comments:
                new_statements.append(transformed_stmt)
            else:
                if not first:
                    new_statements.append(Comment())
                new_statements += Comment.comment_wrap_block(old_code, transformed_stmt.in_assignments + [transformed_stmt])
            first = False

        ast.statements = new_statements
        return ast

    def process_statement_child(self, child: AST):
        if isinstance(child, Expression):
            return self.expr_trafo.visit(child)
        elif child is not None:
            assert isinstance(child, VariableDeclaration)
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
        return ast.replaced_with(MemberAccessExpr(IdentifierExpr(Identifier('msg')), Identifier('sender')), AnnotatedTypeName.address_all())

    def visitLiteralExpr(self, ast: LiteralExpr):
        """ Rule (7) """
        return ast

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        """ Rule (8) """
        if isinstance(ast.idf, HybridArgumentIdf):
            return ast.implicitly_converted(ast.idf.t)
        return ast

    def visitIndexExpr(self, ast: IndexExpr):
        """ Rule (9) """
        return ast.replaced_with(IndexExpr(self.visit(ast.arr), self.visit(ast.index)))

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

    def visitIndexExpr(self, ast: IndexExpr):
        return self.transform_location(ast)

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
