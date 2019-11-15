import re
from copy import deepcopy
from typing import Dict, Optional, List, Tuple

import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_helper import HybridArgumentIdf, CircuitHelper
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.compiler.solidity.fake_solidity_compiler import WS_PATTERN, ID_PATTERN
from zkay.zkay_ast.ast import ReclassifyExpr, Expression, ConstructorOrFunctionDefinition, IfStatement, \
    IdentifierExpr, Parameter, VariableDeclaration, AnnotatedTypeName, StateVariableDeclaration, Mapping, MeExpr, \
    Identifier, VariableDeclarationStatement, ExpressionStatement, \
    UserDefinedTypeName, SourceUnit, ReturnStatement, LocationExpr, AST, \
    Comment, LiteralExpr, Statement, SimpleStatement, FunctionDefinition, IndentBlock, IndexExpr, NumberLiteralExpr, \
    CastExpr, StructDefinition, Array, LabeledBlock, FunctionCallExpr, BuiltinFunction, AssignmentStatement, StatementList
from zkay.zkay_ast.pointers.parent_setter import set_parents
from zkay.zkay_ast.pointers.symbol_table import link_identifiers

proof_param_name = 'proof__'
verification_function_name = 'check_verify'


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

        return StateVariableDeclaration(AnnotatedTypeName(c_type), ['constant'], inst_idf.clone(), CastExpr(c_type, NumberLiteralExpr(0)))

    def visitSourceUnit(self, ast: SourceUnit):
        # Include pki contract
        pki_sv = self.import_contract(ast, cfg.pki_contract_name)

        for c in ast.contracts:
            # Ref pki contract
            ext_var_decls = [pki_sv]

            # Transform types of normal state variables
            c.state_variable_declarations = list(filter(None.__ne__, map(self.var_decl_trafo.visit, c.state_variable_declarations)))

            # Don't have to generate function for internal/private functions which require verification (will always be inlined)
            # TODO external functions
            c.function_definitions = [fdef for fdef in c.function_definitions if 'public' in fdef.modifiers or not fdef.requires_verification]

            # TODO add additional external function for all with not requires_verification and requires_external verification
            # Update all function call exprs to point to internal version

            # Transform function signatures
            for f in c.constructor_definitions + c.function_definitions:
                self.transform_function_signature(f)

            # Transform function body statements
            for f in c.constructor_definitions + c.function_definitions:
                self.transform_function_body(f)
                if self.current_generator.requires_verification():
                    contract_state_var_decl = self.import_contract(ast, f'Verify_{c.idf.name}_{len(ext_var_decls) - 1}_{f.name}')
                    ext_var_decls.append(contract_state_var_decl)

            # Add external contract state variables
            c.state_variable_declarations = Comment.comment_list('External contracts', ext_var_decls) + \
                                            [Comment('User state variables')] + c.state_variable_declarations

            # Transform function definitions
            for f in c.constructor_definitions + c.function_definitions:
                self.transform_function_definition(f)
                circuit = self.circuit_generators[f]
                if circuit.requires_verification():
                    c.struct_definitions.append(StructDefinition(Identifier(f'{f.name}_{cfg.zk_struct_suffix}'), [
                        VariableDeclaration([], AnnotatedTypeName(idf.t), idf.clone(), '')
                        for idf in circuit.output_idfs + circuit.input_idfs
                    ]))

        return ast

    def transform_function_signature(self, ast: ConstructorOrFunctionDefinition):
        circuit_generator = CircuitHelper(ast, ZkayInlineStmtTransformer, ZkayExpressionTransformer, ZkayCircuitTransformer)
        self.circuit_generators[ast] = circuit_generator

        # Check encryption for all private args (if call can come from outside)
        if not ('private' in ast.modifiers or 'internal' in ast.modifiers):
            for p in ast.parameters:
                """ * of T_e rule 8 """
                if p.annotated_type.is_private():
                    circuit_generator.encrypt_parameter(p)

        # Transform parameters
        ast.parameters = list(map(self.var_decl_trafo.visit, ast.parameters))
        if isinstance(ast, FunctionDefinition):
            ast.return_parameters = list(map(self.var_decl_trafo.visit, ast.return_parameters))

    def transform_function_body(self, ast: ConstructorOrFunctionDefinition):
        self.current_generator = self.circuit_generators[ast]

        # Transform body
        ast.original_body = deepcopy(ast.body)
        ast.body = ZkayStatementTransformer(self.current_generator).visit(ast.body)
        return ast

    def transform_function_definition(self, ast: ConstructorOrFunctionDefinition):
        circuit_generator = self.circuit_generators[ast]

        preamble: List[AST] = []
        # Declare return variable if necessary
        if isinstance(ast, FunctionDefinition) and ast.return_parameters:
            assert len(ast.return_parameters) == 1  # for now
            preamble += Comment.comment_list("Declare return variable", [
                Identifier(cfg.return_var_name).decl_var(ast.return_parameters[0].annotated_type)
            ])

        if not circuit_generator.requires_verification():
            if ast.body.statements and isinstance(ast.body.statements[-1], Comment):
                # Remove superfluous empty line
                ast.body.statements.pop()
            ast.body.statements = preamble + ast.body.statements
        else:
            if not ast.has_side_effects:
                for idx, mod in enumerate(ast.modifiers):
                    if mod == 'pure' or mod == 'view':
                        ast.modifiers.remove(mod)
                        break

            zk_struct_type = UserDefinedTypeName([Identifier(f'{ast.name}_{cfg.zk_struct_suffix}')])
            preamble += [Identifier(cfg.zk_data_var_name).decl_var(zk_struct_type), Comment()]

            # Deserialize out array (if any)
            deserialize_stmts = []
            offset = 0
            for s in circuit_generator.output_idfs:
                deserialize_stmts += [s.deserialize(cfg.zk_out_name, offset)]
                offset += s.t.size_in_uints
            if deserialize_stmts:
                ast.add_param(Array(AnnotatedTypeName.uint_all(), offset), cfg.zk_out_name)
                deserialize_stmts = [LabeledBlock(Comment.comment_wrap_block("Deserialize output values", deserialize_stmts), 'exclude')]

            # Add proof parameter
            ast.add_param(AnnotatedTypeName.proof_type(), proof_param_name)

            # Serialize in parameters to in array (if any)
            serialize_stmts = []
            offset = 0
            for s in circuit_generator.input_idfs:
                serialize_stmts += [s.serialize(cfg.zk_in_name, offset)]
                offset += s.t.size_in_uints
            if serialize_stmts:
                serialize_stmts = Comment.comment_wrap_block('Serialize input values', [
                    Identifier(cfg.zk_in_name).decl_var(Array(AnnotatedTypeName.uint_all(), offset))
                ] + serialize_stmts)

            # Call to verifier
            verifier = IdentifierExpr(get_contract_instance_idf(circuit_generator.verifier_contract_type.code()))
            verifier_args = [IdentifierExpr(proof_param_name)]
            verifier_args += [IdentifierExpr(name) for name, _ in circuit_generator.public_arg_arrays]
            verify = ExpressionStatement(verifier.call(verification_function_name, verifier_args))

            # Assemble new body (public key requests, transformed statements, verification invocation)
            ast.body.statements = preamble + \
                                  deserialize_stmts + \
                                  Comment.comment_wrap_block('Backup private arguments for verification',
                                                             circuit_generator.param_to_in_assignments) + \
                                  [IndentBlock("BODY", ast.body.statements)] + \
                                  Comment.comment_wrap_block('Request required public keys',
                                                             circuit_generator.public_key_requests) + \
                                  serialize_stmts + \
                                  [LabeledBlock([Comment('Verify zk proof of execution'), verify], 'exclude')]

        # Add return statement at the end if necessary
        # (was previously replaced by assignment to return_var by ZkayStatementTransformer)
        if circuit_generator.has_return_var:
            ast.body.statements.append(ReturnStatement(IdentifierExpr(cfg.return_var_name)))


class ZkayVarDeclTransformer(AstTransformerVisitor):
    """ Transformer for types, which was left out in the paper """

    def __init__(self):
        super().__init__()
        self.expr_trafo = ZkayExpressionTransformer(None)

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
        new_t = AnnotatedTypeName.cipher_type() if ast.is_private() else AnnotatedTypeName(self.visit(ast.type_name.clone()))
        if ast.is_private():
            new_t.old_priv_text = f'{ast.code()}' if ast.type_name != new_t.type_name else f'@{ast.privacy_annotation.code()}'
        return new_t

    def visitVariableDeclaration(self, ast: VariableDeclaration):
        ast.keywords = [k for k in ast.keywords if k != 'final']
        if ast.annotated_type.is_private():
            ast.storage_location = 'memory'
        return self.visit_children(ast)

    def visitParameter(self, ast: Parameter):
        ast.original_type = ast.annotated_type
        if ast.annotated_type.is_private():
            ast.storage_location = 'memory'
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
        assert not self.gen.has_return_var
        self.gen.has_return_var = True
        return ast.replaced_with(IdentifierExpr(cfg.return_var_name).assign(self.expr_trafo.visit(ast.expr)))

    def visitStatementList(self, ast: StatementList):
        """ Rule (1) """
        new_statements = []
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
                new_statements += Comment.comment_wrap_block(old_code, transformed_stmt.in_assignments + transformed_stmt.pre_statements + [transformed_stmt])

        if new_statements and not isinstance(new_statements[-1], Comment) and isinstance(ast.parent, ConstructorOrFunctionDefinition):
            new_statements.append(Comment())
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


class ZkayInlineStmtTransformer(ZkayStatementTransformer):
    def visitReturnStatement(self, ast: ReturnStatement):
        if ast.expr is None:
            return None
        assert isinstance(ast.function, FunctionDefinition)
        assert len(ast.function.return_parameters) == 1
        expr = self.expr_trafo.visit(ast.expr)
        return self.gen.create_temporary_variable(cfg.return_var_name, ast.function.return_parameters[0].annotated_type, expr)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        vardecl = self.var_decl_trafo.visit(ast.variable_declaration)
        expr = self.expr_trafo.visit(ast.expr)
        return self.gen.create_temporary_variable(vardecl.idf.name, vardecl.annotated_type, expr)


class ZkayExpressionTransformer(AstTransformerVisitor):
    """ Corresponds to T_L / T_e from paper (parameter encryption checks are handled outside of this) """

    def __init__(self, current_generator: Optional[CircuitHelper]):
        super().__init__()
        self.gen = current_generator

    @staticmethod
    def visitMeExpr(ast: MeExpr):
        return ast.replaced_with(IdentifierExpr('msg').dot('sender').as_type(AnnotatedTypeName.address_all()))

    def visitLiteralExpr(self, ast: LiteralExpr):
        """ Rule (7) """
        return ast

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        """ Rule (8) """
        ast.idf = self.gen.get_remapped_idf(ast.idf)
        #if isinstance(ast.idf, HybridArgumentIdf):
        #    return ast.implicitly_converted(ast.idf.t)
        return ast

    def visitIndexExpr(self, ast: IndexExpr):
        """ Rule (9) """
        return ast.replaced_with(self.visit(ast.arr).index(self.visit(ast.key)))

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        """ Rule (11) """
        return self.gen.move_out(ast.expr, ast.privacy)

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            if ast.func.is_private:
                """ Modified Rule (12) (priv expression on its own does not trigger verification) """
                return self.gen.move_out(ast, Expression.me_expr())
            else:
                """ Rule (10) """
                return self.visit_children(ast)

        if isinstance(ast.func, LocationExpr):
            fdef = ast.func.target
            if fdef.requires_verification_if_external: # TODO don't inline funcitons which only require external verification
                if fdef.has_side_effects:
                    raise NotImplementedError('Side effects in inlined functions not yet supported (have to make sure evaluation order matches solidity semantics)')
                # TODO inline
                return self.gen.inline_function(ast, fdef)
                raise NotImplementedError('Calls to functions which require verification not yet supported')
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
        ast.idf = self.gen.get_remapped_idf(ast.idf)
        if isinstance(ast.idf, HybridArgumentIdf):
            return ast
        else:
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

    # INLINED FUNCTION CALLS

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            return self.visit_children(ast)
        # TODO inline (make sure that possible in type checker)
        fdef = ast.func.target
        assert isinstance(fdef, FunctionDefinition)
        assert fdef.return_parameters
        assert fdef.has_static_body

        return self.gen.inline_circuit_function(ast, fdef)

    def visitReturnStatement(self, ast: ReturnStatement):
        assert ast.expr is not None
        self.gen.create_circuit_temp_var_decl(Identifier(cfg.return_var_name).decl_var(ast.expr.annotated_type.type_name, ast.expr))

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        self.gen.create_assignment(ast)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        self.gen.create_circuit_temp_var_decl(ast)

    def visitStatement(self, ast: Statement):
        raise NotImplementedError("Unsupported statement")
