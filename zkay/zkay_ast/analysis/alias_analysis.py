from contextlib import contextmanager
from typing import ContextManager

from zkay.zkay_ast.analysis.partition_state import PartitionState
from zkay.zkay_ast.analysis.side_effects import has_side_effects
from zkay.zkay_ast.ast import VariableDeclarationStatement, IfStatement, \
    Block, ExpressionStatement, MeExpr, AssignmentStatement, RequireStatement, AllExpr, ReturnStatement, \
    FunctionCallExpr, BuiltinFunction, ConstructorOrFunctionDefinition, StatementList, WhileStatement, ForStatement, \
    ContinueStatement, BreakStatement, DoWhileStatement, LocationExpr, TupleExpr, PrivacyLabelExpr
from zkay.zkay_ast.visitor.visitor import AstVisitor


def alias_analysis(ast):
    v = AliasAnalysisVisitor()
    v.visit(ast)


class AliasAnalysisVisitor(AstVisitor):

    def __init__(self, log=False):
        super().__init__('node-or-children', log)
        self.cond_analyzer = GuardConditionAnalyzer()

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        s: PartitionState[PrivacyLabelExpr] = PartitionState()
        s.insert(MeExpr().privacy_annotation_label())
        s.insert(AllExpr().privacy_annotation_label())
        for d in ast.parent.state_variable_declarations:
            s.insert(d.idf)
        for p in ast.parameters:
            s.insert(p.idf)
        ast.body.before_analysis = s
        return self.visit(ast.body)

    def propagate(self, statements, before_analysis: PartitionState[PrivacyLabelExpr]) -> PartitionState[PrivacyLabelExpr]:
        last = before_analysis.copy()
        # push state through each statement
        for statement in statements:
            statement.before_analysis = last
            # print('before', statement, last)
            self.visit(statement)
            last = statement.after_analysis
        # print('after', statement, last)
        return last.copy()

    def visitStatementList(self, ast: StatementList):
        ast.after_analysis = self.propagate(ast.statements, ast.before_analysis)

    def visitBlock(self, ast: Block):
        last = ast.before_analysis.copy()

        # add fresh names from this block
        for name in ast.names.values():
            last.insert(name)

        ast.after_analysis = self.propagate(ast.statements, last)

        # remove names falling out of scope
        for name in ast.names.values():
            ast.after_analysis.remove(name)

    def visitIfStatement(self, ast: IfStatement):
        # condition
        before_then = self.cond_analyzer.analyze(ast.condition, ast.before_analysis)

        # then
        ast.then_branch.before_analysis = before_then
        self.visit(ast.then_branch)
        after_then = ast.then_branch.after_analysis

        # else
        if ast.else_branch:
            before_else = self.cond_analyzer.analyze(ast.condition.unop('!'), ast.before_analysis)
            ast.else_branch.before_analysis = before_else
            self.visit(ast.else_branch)
            after_else = ast.else_branch.after_analysis
        else:
            after_else = ast.before_analysis

        # join branches
        ast.after_analysis = after_then.join(after_else)

    def visitWhileStatement(self, ast: WhileStatement):
        # Body always executes after the condition, but it is also possible that it is not executed at all
        # Condition is true before the body
        # After the loop, the condition is false

        if has_side_effects(ast.condition) or has_side_effects(ast.body):
            ast.before_analysis = ast.before_analysis.separate_all()

        before_body = self.cond_analyzer.analyze(ast.condition, ast.before_analysis)
        ast.body.before_analysis = before_body
        self.visit(ast.body)

        # Either no loop iteration or at least one loop iteration
        skip_loop = self.cond_analyzer.analyze(ast.condition.unop('!'), ast.before_analysis)
        did_loop = self.cond_analyzer.analyze(ast.condition.unop('!'), ast.body.after_analysis)

        # join
        ast.after_analysis = skip_loop.join(did_loop)

    def visitDoWhileStatement(self, ast: DoWhileStatement):
        # Body either executes with or without condition, but it is also possible that it is not executed at all
        # No information about condition before the body
        # After the loop, the condition is false

        # Could be subsequent loop iteration after condition with side effect
        cond_se = has_side_effects(ast.condition)
        if cond_se or has_side_effects(ast.body):
            ast.before_analysis = ast.before_analysis.separate_all()

        ast.body.before_analysis = ast.before_analysis.copy()
        self.visit(ast.body)

        # ast.before_analysis is only used by expressions inside condition -> body has already happened at that point
        ast.before_analysis = ast.body.after_analysis.copy()
        ast.after_analysis = self.cond_analyzer.analyze(ast.condition.unop('!'), ast.before_analysis)

    def visitForStatement(self, ast: ForStatement):
        last = ast.before_analysis.copy()

        # add names introduced in init
        for name in ast.names.values():
            last.insert(name)

        if ast.init is not None:
            ast.init.before_analysis = last.copy()
            self.visit(ast.init)
            ast.before_analysis = ast.init.after_analysis.copy() # init should be taken into account when looking up things in the condition

        if has_side_effects(ast.condition) or has_side_effects(ast.body) or (ast.update is not None and has_side_effects(ast.update)):
            ast.before_analysis = last.separate_all()

        ast.body.before_analysis = self.cond_analyzer.analyze(ast.condition, ast.before_analysis)
        self.visit(ast.body)
        if ast.update is not None:
            # Update is always executed after the body (if it is executed)
            ast.update.before_analysis = ast.body.after_analysis.copy()
            self.visit(ast.update)

        skip_loop = self.cond_analyzer.analyze(ast.condition.unop('!'), ast.init.after_analysis)
        did_loop = self.cond_analyzer.analyze(ast.condition.unop('!'), ast.update.after_analysis if ast.update else ast.body.after_analysis)

        # join
        ast.after_analysis = skip_loop.join(did_loop)

        # drop names introduced in init
        for name in ast.names.values():
            ast.after_analysis.remove(name)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        e = ast.expr
        if e and has_side_effects(e):
            ast.before_analysis = ast.before_analysis.separate_all()

        # visit expression
        if e:
            self.visit(e)

        # state after declaration
        after = ast.before_analysis.copy()

        # name of variable is already in list
        name = ast.variable_declaration.idf
        assert (after.has(name))

        # make state more precise
        if e and e.privacy_annotation_label():
            after.merge(name, e.privacy_annotation_label())

        ast.after_analysis = after

    def visitRequireStatement(self, ast: RequireStatement):
        if has_side_effects(ast.condition):
            ast.before_analysis = ast.before_analysis.separate_all()

        self.visit(ast.condition)

        # state after require
        after = ast.before_analysis.copy()

        # make state more precise
        c = ast.condition
        if isinstance(c, FunctionCallExpr) and isinstance(c.func, BuiltinFunction) and c.func.op == '==':
            lhs = c.args[0].privacy_annotation_label()
            rhs = c.args[1].privacy_annotation_label()
            if lhs and rhs:
                after.merge(lhs, rhs)

        ast.after_analysis = after

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        lhs = ast.lhs
        rhs = ast.rhs
        if has_side_effects(lhs) or has_side_effects(rhs):
            ast.before_analysis = ast.before_analysis.separate_all()

        # visit expression
        self.visit(ast.lhs)
        self.visit(ast.rhs)

        # state after assignment
        after = ast.before_analysis.copy()
        recursive_assign(lhs, rhs, after)

        # save state
        ast.after_analysis = after

    def visitExpressionStatement(self, ast: ExpressionStatement):
        if has_side_effects(ast.expr):
            ast.before_analysis = ast.before_analysis.separate_all()

        # visit expression
        self.visit(ast.expr)

        # if expression has effect, we are already at TOP
        ast.after_analysis = ast.before_analysis.copy()

    def visitReturnStatement(self, ast: ReturnStatement):
        ast.after_analysis = ast.before_analysis

    def visitContinueStatement(self, ast: ContinueStatement):
        ast.after_analysis = ast.before_analysis

    def visitBreakStatement(self, ast: BreakStatement):
        ast.after_analysis = ast.before_analysis

    def visitStatement(self, _):
        raise NotImplementedError()


class GuardConditionAnalyzer(AstVisitor):
    def __init__(self, log=False):
        super().__init__('node-or-children', log)
        self._neg = False
        self._analysis = None

    def analyze(self, cond, before_analysis: PartitionState) -> PartitionState:
        if has_side_effects(cond):
            return before_analysis.copy().separate_all()
        else:
            self._neg = False
            self._analysis = before_analysis.copy()
            self.visit(cond)
            return self._analysis

    @contextmanager
    def _negated(self) -> ContextManager:
        self._neg = not self._neg
        yield
        self._neg = not self._neg

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            op = ast.func.op
            if op == '!':
                with self._negated():
                    self.visit(ast.args[0])
            elif (op == '&&' and not self._neg) or (op == '||' and self._neg):
                self.visit(ast.args[0])
                self.visit(ast.args[1])
            elif op == 'parenthesis':
                self.visit(ast.args[0])
            elif (op == '==' and not self._neg) or (op == '!=' and self._neg):
                recursive_merge(ast.args[0], ast.args[1], self._analysis)


def _recursive_update(lhs, rhs, analysis: PartitionState, merge: bool):
    if isinstance(lhs, TupleExpr) and isinstance(rhs, TupleExpr):
        for l, r in zip(lhs.elements, rhs.elements):
            _recursive_update(l, r, analysis, merge)
    else:
        lhs = lhs.privacy_annotation_label()
        rhs = rhs.privacy_annotation_label()
        if lhs and rhs and analysis.has(rhs):
            if merge:
                analysis.merge(lhs, rhs)
            else:
                analysis.move_to(lhs, rhs)
        elif lhs:
            analysis.move_to_separate(lhs)


def recursive_merge(lhs, rhs, analysis: PartitionState):
    _recursive_update(lhs, rhs, analysis, True)


def recursive_assign(lhs, rhs, analysis: PartitionState):
    _recursive_update(lhs, rhs, analysis, False)
