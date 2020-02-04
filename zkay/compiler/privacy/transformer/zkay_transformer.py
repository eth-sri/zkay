import re
from typing import Optional

from zkay.compiler.privacy.circuit_generation.circuit_helper import HybridArgumentIdf, CircuitHelper
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.solidity.fake_solidity_generator import WS_PATTERN, ID_PATTERN
from zkay.config import cfg
from zkay.type_check.type_checker import TypeCheckVisitor
from zkay.zkay_ast.analysis.contains_private_checker import contains_private_expr
from zkay.zkay_ast.ast import ReclassifyExpr, Expression, IfStatement, StatementList, HybridArgType, BlankLine, \
    IdentifierExpr, Parameter, VariableDeclaration, AnnotatedTypeName, StateVariableDeclaration, Mapping, MeExpr, \
    Identifier, VariableDeclarationStatement, ReturnStatement, LocationExpr, AST, AssignmentStatement, Block, \
    Comment, LiteralExpr, Statement, SimpleStatement, IndexExpr, FunctionCallExpr, BuiltinFunction, TupleExpr, NumberLiteralExpr, \
    MemberAccessExpr, WhileStatement, BreakStatement, ContinueStatement, ForStatement, DoWhileStatement, \
    BooleanLiteralType, NumberLiteralType, BooleanLiteralExpr, PrimitiveCastExpr, EnumDefinition
from zkay.zkay_ast.visitor.deep_copy import replace_expr


class ZkayVarDeclTransformer(AstTransformerVisitor):
    """ Transformer for types, which was left out in the paper """

    def __init__(self):
        super().__init__()
        self.expr_trafo = ZkayExpressionTransformer(None)

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
        new_t = AnnotatedTypeName.cipher_type() if ast.is_private() else AnnotatedTypeName(self.visit(ast.type_name.clone()))
        new_t.declared_type = ast.clone()
        return new_t

    def visitVariableDeclaration(self, ast: VariableDeclaration):
        ast.keywords = [k for k in ast.keywords if k != 'final']
        if ast.annotated_type.is_private():
            ast.storage_location = 'memory'
        return self.visit_children(ast)

    def visitParameter(self, ast: Parameter):
        ast.keywords = [k for k in ast.keywords if k != 'final']
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
        if ast.condition.annotated_type.is_public():
            if contains_private_expr(ast.then_branch) or contains_private_expr(ast.else_branch):
                guard_var, ast.condition = self.gen.add_to_circuit_inputs(ast.condition)
                with self.gen.guarded(guard_var, True):
                    ast.then_branch = self.visit(ast.then_branch)
                if ast.else_branch is not None:
                    with self.gen.guarded(guard_var, False):
                        ast.else_branch = self.visit(ast.else_branch)
            else:
                ast.condition = self.expr_trafo.visit(ast.condition)
                ast.then_branch = self.visit(ast.then_branch)
                if ast.else_branch is not None:
                    ast.else_branch = self.visit(ast.else_branch)
            return ast
        else:
            return self.gen.evaluate_stmt_in_circuit(ast)

    def visitWhileStatement(self, ast: WhileStatement):
        assert not contains_private_expr(ast.condition)
        assert not contains_private_expr(ast.body)
        return ast

    def visitDoWhileStatement(self, ast: DoWhileStatement):
        assert not contains_private_expr(ast.condition)
        assert not contains_private_expr(ast.body)
        return ast

    def visitForStatement(self, ast: ForStatement):
        if ast.init is not None:
            ast.init = self.visit(ast.init)
            ast.pre_statements += ast.init.pre_statements
        assert not contains_private_expr(ast.condition)
        assert not ast.update or not contains_private_expr(ast.update)
        assert not contains_private_expr(ast.body) # OR fixed size loop -> static analysis can prove that loop terminates in fixed # iterations
        return ast

    def visitContinueStatement(self, ast: ContinueStatement):
        return ast

    def visitBreakStatement(self, ast: BreakStatement):
        return ast

    def visitReturnStatement(self, ast: ReturnStatement):
        if ast.function.requires_verification:
            if ast.expr is None:
                return None
            assert not self.gen.has_return_var
            self.gen.has_return_var = True
            expr = self.expr_trafo.visit(ast.expr)
            ret_args = [IdentifierExpr(vd.idf.clone()).override(target=vd) for vd in ast.function.return_var_decls]
            return TupleExpr(ret_args).assign(expr).override(pre_statements=ast.pre_statements)
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
        return replace_expr(ast, IdentifierExpr('msg').dot('sender')).as_type(AnnotatedTypeName.address_all())

    def visitLiteralExpr(self, ast: LiteralExpr):
        """ Rule (7) """
        return ast

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        """ Rule (8) """
        return ast

    def visitIndexExpr(self, ast: IndexExpr):
        """ Rule (9) """
        return replace_expr(ast, self.visit(ast.arr).index(self.visit(ast.key)))

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        return self.visit_children(ast)

    def visitTupleExpr(self, ast: TupleExpr):
        return self.visit_children(ast)

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        """ Rule (11) """
        return self.gen.evaluate_expr_in_circuit(ast.expr, ast.privacy.privacy_annotation_label())

    def visit_guarded_expression(self, guard_var: HybridArgumentIdf, if_true: bool, expr: Expression):
        prelen = len(expr.statement.pre_statements)
        with self.gen.guarded(guard_var, if_true):
            ret = self.visit(expr)
        new_pre_stmts = expr.statement.pre_statements[prelen:]
        if new_pre_stmts:
            if guard_var.arg_type == HybridArgType.TMP_CIRCUIT_VAL:
                assert isinstance(guard_var.corresponding_priv_expression.annotated_type.type_name, BooleanLiteralType)
                cond_expr = BooleanLiteralExpr(guard_var.corresponding_priv_expression.annotated_type.type_name.value ^ (not if_true))
            else:
                cond_expr = guard_var.get_loc_expr() if if_true else guard_var.get_loc_expr().unop('!')
            expr.statement.pre_statements = expr.statement.pre_statements[:prelen] + [IfStatement(cond_expr, Block(new_pre_stmts), None)]
        return ret

    def visitBuiltinFunction(self, ast: BuiltinFunction):
        return ast

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            if ast.func.is_private:
                """ Modified Rule (12) (priv expression on its own does not trigger verification) """
                return self.gen.evaluate_expr_in_circuit(ast, Expression.me_expr())
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
        elif ast.is_cast:
            assert isinstance(ast.func.target, EnumDefinition)
            if ast.args[0].evaluate_privately:
                return self.gen.evaluate_expr_in_circuit(ast, Expression.me_expr())
            else:
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

    def visitPrimitiveCastExpr(self, ast: PrimitiveCastExpr):
        if ast.evaluate_privately:
            return self.gen.evaluate_expr_in_circuit(ast, Expression.me_expr())
        else:
            return self.visit_children(ast)

    def visitExpression(self, ast: Expression):
        raise NotImplementedError()


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
        if not isinstance(ast.idf, HybridArgumentIdf):
            ast = self.gen.get_remapped_idf_expr(ast)
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
        if ast.expr.evaluate_privately:
            return self.visit(ast.expr)
        else:
            assert ast.expr.annotated_type.is_public()
            return self.gen.add_to_circuit_inputs(ast.expr)[1]

    def visitExpression(self, ast: Expression):
        """ Rule (16) """
        return self.visit_children(ast)

    # INLINED FUNCTION CALLS

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        t = ast.annotated_type.type_name

        # Constant folding
        if isinstance(t, BooleanLiteralType):
            return replace_expr(ast, BooleanLiteralExpr(t.value))
        elif isinstance(t, NumberLiteralType):
            return replace_expr(ast, NumberLiteralExpr(t.value))

        if isinstance(ast.func, BuiltinFunction):
            return self.visit_children(ast)

        fdef = ast.func.target
        assert fdef.is_function
        assert fdef.return_parameters
        assert fdef.has_static_body

        return self.gen.inline_function_call_into_circuit(ast)

    def visitReturnStatement(self, ast: ReturnStatement):
        assert ast.expr is not None
        if not isinstance(ast.expr, TupleExpr):
            ast.expr = TupleExpr([ast.expr])

        for vd, expr in zip(ast.function.return_var_decls, ast.expr.elements):
            self.gen.create_new_idf_version_from_value(vd.idf, expr)

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        self.gen.add_assignment_to_circuit(ast)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        if ast.expr is None:
            t = ast.variable_declaration.annotated_type.type_name
            assert t.can_be_private()
            ast.expr = TypeCheckVisitor.implicitly_converted_to(NumberLiteralExpr(0).override(parent=ast, statement=ast), t.clone())
        self.gen.create_new_idf_version_from_value(ast.variable_declaration.idf, ast.expr)

    def visitIfStatement(self, ast: IfStatement):
        self.gen.add_if_statement_to_circuit(ast)

    def visitBlock(self, ast: Block):
        self.gen.add_block_to_circuit(ast)

    def visitStatement(self, ast: Statement):
        raise NotImplementedError("Unsupported statement")
