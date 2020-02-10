"""
This module defines zkay->solidity transformers for the smaller contract elements (statements, expressions, state variables).
"""

import re
from typing import Optional

from zkay.compiler.privacy.circuit_generation.circuit_helper import HybridArgumentIdf, CircuitHelper
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.solidity.fake_solidity_generator import WS_PATTERN, ID_PATTERN
from zkay.config import cfg
from zkay.zkay_ast.analysis.contains_private_checker import contains_private_expr
from zkay.zkay_ast.ast import ReclassifyExpr, Expression, IfStatement, StatementList, HybridArgType, BlankLine, \
    IdentifierExpr, Parameter, VariableDeclaration, AnnotatedTypeName, StateVariableDeclaration, Mapping, MeExpr, \
    VariableDeclarationStatement, ReturnStatement, LocationExpr, AST, AssignmentStatement, Block, \
    Comment, LiteralExpr, Statement, SimpleStatement, IndexExpr, FunctionCallExpr, BuiltinFunction, TupleExpr, NumberLiteralExpr, \
    MemberAccessExpr, WhileStatement, BreakStatement, ContinueStatement, ForStatement, DoWhileStatement, \
    BooleanLiteralType, NumberLiteralType, BooleanLiteralExpr, PrimitiveCastExpr, EnumDefinition, EncryptionExpression
from zkay.zkay_ast.visitor.deep_copy import replace_expr


class ZkayVarDeclTransformer(AstTransformerVisitor):
    """
    Transformer for types, which was left out in the paper.

    This removes all privacy labels and converts the types of non-public variables (not @all)
    to cipher_type. A copy of the original type (pre-transformation) is stored in the AnnotatedTypeName's declared_type field.

    If the declared_type is different from the actual type, code generation will insert an inline block comment with the original
    privacy label and/or type (whatever is different from the actual type).
    """

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
        # make sure every state var gets a public getter (required for simulation)
        ast.keywords.append('public')
        ast.expr = self.expr_trafo.visit(ast.expr)
        return self.visit_children(ast)

    def visitMapping(self, ast: Mapping):
        if ast.key_label is not None:
            ast.key_label = ast.key_label.name
        return self.visit_children(ast)


class ZkayStatementTransformer(AstTransformerVisitor):
    """Corresponds to T from paper, (with additional handling of return statement and loops)."""

    def __init__(self, current_gen: CircuitHelper):
        super().__init__()
        self.gen = current_gen
        self.expr_trafo = ZkayExpressionTransformer(self.gen)
        self.var_decl_trafo = ZkayVarDeclTransformer()

    def visitStatementList(self, ast: StatementList):
        """
        Rule (1)

        All statements are transformed individually.
        Whenever the transformation of a statement requires the introduction of additional statements
        (the CircuitHelper indicates this by storing them in the statement's pre_statements list), they are prepended to the transformed
        statement in the list.

        If transformation changes the appearance of a statement (apart from type changes),
        the statement is wrapped in a comment block which displays the original statement's code.
        """
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
        """Default statement child handling. Expressions and declarations are visited by the corresponding transformers."""
        if isinstance(child, Expression):
            return self.expr_trafo.visit(child)
        elif child is not None:
            assert isinstance(child, VariableDeclaration)
            return self.var_decl_trafo.visit(child)

    def visitStatement(self, ast: Statement):
        """
        Rules (3), (4)

        This is for all the statements where the statements themselves remain untouched and only the children are altered.
        """
        assert isinstance(ast, SimpleStatement) or isinstance(ast, VariableDeclarationStatement)
        ast.process_children(self.process_statement_child)
        return ast

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        """Rule (2)"""
        ast.lhs = self.expr_trafo.visit(ast.lhs)
        ast.rhs = self.expr_trafo.visit(ast.rhs)
        modvals = ast.modified_values
        if cfg.opt_cache_circuit_outputs and isinstance(ast.lhs, IdentifierExpr) and isinstance(ast.rhs, MemberAccessExpr):
            # Skip invalidation if rhs is circuit output
            if isinstance(ast.rhs.member, HybridArgumentIdf) and ast.rhs.member.arg_type == HybridArgType.PUB_CIRCUIT_ARG:
                modvals = [mv for mv in modvals if mv.target != ast.lhs.target]
                if isinstance(ast.rhs.member.corresponding_priv_expression, EncryptionExpression):
                    ridf = ast.rhs.member.corresponding_priv_expression.expr.idf
                else:
                    ridf = ast.rhs.member.corresponding_priv_expression.idf
                assert isinstance(ridf, HybridArgumentIdf)
                self.gen._remapper.remap(ast.lhs.target.idf, ridf)

        if self.gen is not None:
            # Invalidate circuit value for assignment targets
            for val in modvals:
                if val.key is None:
                    self.gen.invalidate_idf(val.target.idf)
        return ast

    def visitIfStatement(self, ast: IfStatement):
        """
        Rule (6) + additional support for private conditions

        If the condition is public, guard conditions are introduced for both branches if any of the branches contains private expressions.

        If the condition is private, the whole if statement is inlined into the circuit. The only side-effects which are allowed
        inside the branch bodies are assignment statements with an lhs@me. (anything else would leak private information).
        The if statement will be replaced by an assignment statement where the lhs is a tuple of all locations which are written
        in either branch and rhs is a tuple of the corresponding circuit outputs.
        """
        if ast.condition.annotated_type.is_public():
            if contains_private_expr(ast.then_branch) or contains_private_expr(ast.else_branch):
                before_if_state = self.gen._remapper.get_state()
                guard_var = self.gen.add_to_circuit_inputs(ast.condition)
                ast.condition = guard_var.get_loc_expr(ast)
                with self.gen.guarded(guard_var, True):
                    ast.then_branch = self.visit(ast.then_branch)
                    self.gen._remapper.set_state(before_if_state)
                if ast.else_branch is not None:
                    with self.gen.guarded(guard_var, False):
                        ast.else_branch = self.visit(ast.else_branch)
                        self.gen._remapper.set_state(before_if_state)

                # Invalidate values modified in either branch
                for val in ast.modified_values:
                    if val.key is None:
                        self.gen.invalidate_idf(val.target.idf)
            else:
                ast.condition = self.expr_trafo.visit(ast.condition)
                ast.then_branch = self.visit(ast.then_branch)
                if ast.else_branch is not None:
                    ast.else_branch = self.visit(ast.else_branch)
            return ast
        else:
            return self.gen.evaluate_stmt_in_circuit(ast)

    def visitWhileStatement(self, ast: WhileStatement):
        # Loops must always be purely public
        assert not contains_private_expr(ast.condition)
        assert not contains_private_expr(ast.body)
        return ast

    def visitDoWhileStatement(self, ast: DoWhileStatement):
        # Loops must always be purely public
        assert not contains_private_expr(ast.condition)
        assert not contains_private_expr(ast.body)
        return ast

    def visitForStatement(self, ast: ForStatement):
        if ast.init is not None:
            # Init is the only part of a for loop which may contain private expressions
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
        """
        Handle return statement.

        If the function requires verification, the return statement is replaced by an assignment to a return variable.
        (which will be returned at the very end of the function body, after any verification wrapper code).
        Otherwise only the expression is transformed.
        """
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
        """Fail if there are any untransformed expressions left."""
        raise RuntimeError(f"Missed an expression of type {type(ast)}")


class ZkayExpressionTransformer(AstTransformerVisitor):
    """
    Roughly corresponds to T_L / T_e from paper.

    T_L and T_e are equivalent here, because parameter encryption checks are handled in the verification wrapper of the function body.
    In addition to the features described in the paper, this transformer also supports primitive type casting,
    tuples (multiple return values), operations with short-circuiting and function calls.
    """

    def __init__(self, current_generator: Optional[CircuitHelper]):
        super().__init__()
        self.gen = current_generator

    @staticmethod
    def visitMeExpr(ast: MeExpr):
        """Replace me with msg.sender."""
        return replace_expr(ast, IdentifierExpr('msg').dot('sender')).as_type(AnnotatedTypeName.address_all())

    def visitLiteralExpr(self, ast: LiteralExpr):
        """Rule (7), don't modify constants."""
        return ast

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        """Rule (8), don't modify identifiers."""
        return ast

    def visitIndexExpr(self, ast: IndexExpr):
        """Rule (9), transform location and index expressions separately."""
        return replace_expr(ast, self.visit(ast.arr).index(self.visit(ast.key)))

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        return self.visit_children(ast)

    def visitTupleExpr(self, ast: TupleExpr):
        return self.visit_children(ast)

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        """
        Rule (11), trigger a boundary crossing.

        The reclassified expression is evaluated in the circuit and its result is made available in solidity.
        """
        return self.gen.evaluate_expr_in_circuit(ast.expr, ast.privacy.privacy_annotation_label())

    def visitBuiltinFunction(self, ast: BuiltinFunction):
        return ast

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            if ast.func.is_private:
                """
                Modified Rule (12) builtin functions with private operands are evaluated inside the circuit.

                A private expression on its own (like an IdentifierExpr referring to a private variable) is not enough to trigger a
                boundary crossing (assignment of private variables is a public operation).
                """
                return self.gen.evaluate_expr_in_circuit(ast, Expression.me_expr())
            else:
                """
                Rule (10) with additional short-circuit handling.

                Builtin operations on public operands are normally left untransformed, but if the builtin function has
                short-circuiting semantics, guard conditions must be added if any of the public operands contains
                nested private expressions.
                """
                # handle short-circuiting
                if ast.func.has_shortcircuiting() and any(map(contains_private_expr, ast.args[1:])):
                    op = ast.func.op
                    guard_var = self.gen.add_to_circuit_inputs(ast.args[0])
                    ast.args[0] = guard_var.get_loc_expr(ast)
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
            """Casts are handled either in public or inside the circuit depending on the privacy of the casted expression."""
            assert isinstance(ast.func.target, EnumDefinition)
            if ast.args[0].evaluate_privately:
                return self.gen.evaluate_expr_in_circuit(ast, Expression.me_expr())
            else:
                return self.visit_children(ast)
        else:
            """
            Handle normal function calls (outside private expression case).

            The called functions are allowed to have side effects,
            if the function does not require verification it can even be recursive.
            """
            assert isinstance(ast.func, LocationExpr)
            ast = self.visit_children(ast)
            if ast.func.target.requires_verification_when_external:
                # Reroute the function call to the corresponding internal function if the called function was split into external/internal.
                if not isinstance(ast.func, IdentifierExpr):
                    raise NotImplementedError()
                ast.func.idf.name = cfg.get_internal_name(ast.func.target)

            if ast.func.target.requires_verification:
                # If the target function has an associated circuit, make this function's circuit aware of the call.
                self.gen.call_function(ast)
            elif ast.func.target.has_side_effects and self.gen is not None:
                # Invalidate modified state variables for the current circuit
                for val in ast.modified_values:
                    if val.key is None and isinstance(val.target, StateVariableDeclaration):
                        self.gen.invalidate_idf(val.target.idf)

            # The call will be present as a normal function call in the output solidity code.
            return ast

    def visit_guarded_expression(self, guard_var: HybridArgumentIdf, if_true: bool, expr: Expression):
        prelen = len(expr.statement.pre_statements)

        # Transform expression with guard condition in effect
        with self.gen.guarded(guard_var, if_true):
            ret = self.visit(expr)

        # If new pre statements were added, they must be guarded using an if statement in the public solidity code
        new_pre_stmts = expr.statement.pre_statements[prelen:]
        if new_pre_stmts:
            cond_expr = guard_var.get_loc_expr()
            if isinstance(cond_expr, BooleanLiteralExpr):
                cond_expr = BooleanLiteralExpr(cond_expr.value == if_true)
            elif not if_true:
                cond_expr = cond_expr.unop('!')
            expr.statement.pre_statements = expr.statement.pre_statements[:prelen] + [IfStatement(cond_expr, Block(new_pre_stmts), None)]
        return ret

    def visitPrimitiveCastExpr(self, ast: PrimitiveCastExpr):
        """Casts are handled either in public or inside the circuit depending on the privacy of the casted expression."""
        if ast.evaluate_privately:
            return self.gen.evaluate_expr_in_circuit(ast, Expression.me_expr())
        else:
            return self.visit_children(ast)

    def visitExpression(self, ast: Expression):
        raise NotImplementedError()


class ZkayCircuitTransformer(AstTransformerVisitor):
    """
    Corresponds to T_phi from paper.

    This extends the abstract circuit representation while transforming private expressions and statements.
    Private expressions can never have side effects.
    Private statements may contain assignment statements with lhs@me (no other types of side effects are allowed).
    """

    def __init__(self, current_generator: CircuitHelper):
        super().__init__()
        self.gen = current_generator

    def visitLiteralExpr(self, ast: LiteralExpr):
        """Rule (13), don't modify constants."""
        return ast

    def visitIndexExpr(self, ast: IndexExpr):
        return self.transform_location(ast)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if not isinstance(ast.idf, HybridArgumentIdf):
            # If ast is not already transformed, get current SSA version
            ast = self.gen.get_remapped_idf_expr(ast)
        if isinstance(ast, IdentifierExpr) and isinstance(ast.idf, HybridArgumentIdf):
            # The current version of ast.idf is already in the circuit
            assert ast.idf.arg_type != HybridArgType.PUB_CONTRACT_VAL
            return ast
        else:
            # ast is not yet in the circuit -> move it in
            return self.transform_location(ast)

    def transform_location(self, loc: LocationExpr):
        """Rule (14), move location into the circuit."""
        return self.gen.add_to_circuit_inputs(loc).get_idf_expr()

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        """Rule (15), boundary crossing if analysis determined that it is """
        if ast.expr.evaluate_privately:
            return self.visit(ast.expr)
        else:
            assert ast.expr.annotated_type.is_public()
            return self.gen.add_to_circuit_inputs(ast.expr).get_idf_expr()

    def visitExpression(self, ast: Expression):
        """Rule (16), other expressions don't need special treatment."""
        return self.visit_children(ast)

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        t = ast.annotated_type.type_name

        # Constant folding for literal types
        if isinstance(t, BooleanLiteralType):
            return replace_expr(ast, BooleanLiteralExpr(t.value))
        elif isinstance(t, NumberLiteralType):
            return replace_expr(ast, NumberLiteralExpr(t.value))

        if isinstance(ast.func, BuiltinFunction):
            # Builtin functions are supported natively by the circuit
            return self.visit_children(ast)

        fdef = ast.func.target
        assert fdef.is_function
        assert fdef.return_parameters
        assert fdef.has_static_body

        # Function call inside private expression -> entire body will be inlined into circuit.
        # Function must not have side-effects (only pure and view is allowed) and cannot have a nonstatic body (i.e. recursion)
        return self.gen.inline_function_call_into_circuit(ast)

    def visitReturnStatement(self, ast: ReturnStatement):
        self.gen.add_return_stmt_to_circuit(ast)

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        self.gen.add_assignment_to_circuit(ast)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        self.gen.add_var_decl_to_circuit(ast)

    def visitIfStatement(self, ast: IfStatement):
        self.gen.add_if_statement_to_circuit(ast)

    def visitBlock(self, ast: Block, guard_cond: Optional[HybridArgumentIdf] = None, guard_val: Optional[bool] = None):
        self.gen.add_block_to_circuit(ast, guard_cond, guard_val)

    def visitStatement(self, ast: Statement):
        """Fail if statement type was not handled."""
        raise NotImplementedError("Unsupported statement")
