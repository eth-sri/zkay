import re
from typing import Optional

import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_helper import HybridArgumentIdf, CircuitHelper, Guarded
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.solidity.fake_solidity_compiler import WS_PATTERN, ID_PATTERN
from zkay.zkay_ast.analysis.contains_private_checker import contains_private_expr
from zkay.zkay_ast.ast import ReclassifyExpr, Expression, IfStatement, StatementList, HybridArgType, BlankLine, \
    IdentifierExpr, Parameter, VariableDeclaration, AnnotatedTypeName, StateVariableDeclaration, Mapping, MeExpr, \
    Identifier, VariableDeclarationStatement, ReturnStatement, LocationExpr, AST, AssignmentStatement, Block, \
    Comment, LiteralExpr, Statement, SimpleStatement, FunctionDefinition, IndexExpr, FunctionCallExpr, BuiltinFunction


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
                new_statements += Comment.comment_wrap_block(old_code, transformed_stmt.pre_statements + [transformed_stmt])

        if new_statements and isinstance(new_statements[-1], BlankLine):
            new_statements = new_statements[:-1]
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
        assert ast.condition.annotated_type.is_public()
        if contains_private_expr(ast.then_branch) or contains_private_expr(ast.else_branch):
            guard_var, ast.condition = self.gen.add_to_circuit_inputs(ast.condition)
            with Guarded(self.gen, guard_var, True):
                ast.then_branch = self.visit(ast.then_branch)
            if ast.else_branch is not None:
                with Guarded(self.gen, guard_var, False):
                    ast.else_branch = self.visit(ast.else_branch)
        else:
            ast.condition = self.expr_trafo.visit_children(ast.condition)
            ast.then_branch = self.visit(ast.then_branch)
            if ast.else_branch is not None:
                ast.else_branch = self.visit(ast.else_branch)
        return ast

    def visitReturnStatement(self, ast: ReturnStatement):
        if ast.function.requires_verification:
            if ast.expr is None:
                return None
            assert not self.gen.has_return_var
            self.gen.has_return_var = True
            expr = self.expr_trafo.visit(ast.expr)
            return ast.replaced_with(IdentifierExpr(cfg.return_var_name).assign(expr))
        else:
            ast.expr = self.expr_trafo.visit(ast.expr)
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
        return ast.replaced_with(IdentifierExpr('msg').dot('sender').as_type(AnnotatedTypeName.address_all()))

    def visitLiteralExpr(self, ast: LiteralExpr):
        """ Rule (7) """
        return ast

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        """ Rule (8) """
        return ast

    def visitIndexExpr(self, ast: IndexExpr):
        """ Rule (9) """
        return ast.replaced_with(self.visit(ast.arr).index(self.visit(ast.key)))

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        """ Rule (11) """
        return self.gen.get_circuit_output_for_private_expression(ast.expr, ast.privacy.privacy_annotation_label())

    def visit_guarded_expression(self, guard_var: HybridArgumentIdf, if_true: bool, expr: Expression):
        prelen = len(expr.statement.pre_statements)
        with Guarded(self.gen, guard_var, if_true):
            ret = self.visit(expr)
        new_pre_stmts = expr.statement.pre_statements[prelen:]
        if new_pre_stmts:
            cond_expr = guard_var.get_loc_expr() if if_true else guard_var.get_loc_expr().unop('!')
            expr.statement.pre_statements = expr.statement.pre_statements[:prelen] + [IfStatement(cond_expr, Block(new_pre_stmts), None)]
        return ret

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            if ast.func.is_private:
                """ Modified Rule (12) (priv expression on its own does not trigger verification) """
                return self.gen.get_circuit_output_for_private_expression(ast, Expression.me_expr())
            else:
                """ Rule (10) """
                # handle short-circuiting
                if ast.func.has_shortcircuiting() and any(map(contains_private_expr, ast.args[1:])):
                    op = ast.func.op
                    guard_var, ast.args[0] = self.gen.add_to_circuit_inputs(ast.args[0])
                    if op == 'ite':
                        ast.args[1] = self.visit_guarded_expression(guard_var, True, ast.args[1])
                        ast.args[2] = self.visit_guarded_expression(guard_var, False, ast.args[2])
                    elif op == '||':
                        ast.args[1] = self.visit_guarded_expression(guard_var, False, ast.args[1])
                    elif op == '&&':
                        ast.args[1] = self.visit_guarded_expression(guard_var, True, ast.args[1])
                    return ast

                return self.visit_children(ast)
        else:
            assert isinstance(ast.func, LocationExpr)
            ast = self.visit_children(ast)
            if ast.func.target.requires_verification_when_external:
                if not isinstance(ast.func, IdentifierExpr):
                    raise NotImplementedError()
                ast.func.idf.name = cfg.get_internal_name(ast.func.target)

            if ast.func.target.requires_verification:
                self.gen.call_function(ast)
            return ast


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
        ast = self.gen.get_remapped_idf(ast)
        if isinstance(ast, IdentifierExpr) and isinstance(ast.idf, HybridArgumentIdf):
            assert ast.idf.arg_type != HybridArgType.PUB_CONTRACT_VAL
            return ast
        else:
            return self.transform_location(ast)

    def transform_location(self, loc: LocationExpr):
        """ Rule (14) """
        return self.gen.add_to_circuit_inputs(loc)[1]

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

        fdef = ast.func.target
        assert isinstance(fdef, FunctionDefinition)
        assert fdef.return_parameters
        assert fdef.has_static_body
        assert not fdef.has_side_effects or ast.has_side_effects
        assert not ast.has_side_effects

        return self.gen.inline_circuit_function(ast, fdef)

    def visitReturnStatement(self, ast: ReturnStatement):
        assert ast.expr is not None
        e = self.visit(ast.expr)
        ret_var_decl = ast.replaced_with(Identifier(cfg.return_var_name).decl_var(ast.expr.annotated_type.type_name, e))
        self.gen.create_temporary_circuit_variable(ret_var_decl)

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        self.gen.add_assignment_to_circuit(ast)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        self.gen.create_temporary_circuit_variable(ast)

    def visitStatement(self, ast: Statement):
        raise NotImplementedError("Unsupported statement")
