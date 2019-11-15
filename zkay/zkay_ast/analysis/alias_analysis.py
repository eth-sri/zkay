from zkay.zkay_ast.analysis.partition_state import PartitionState
from zkay.zkay_ast.analysis.side_effects import has_side_effects
from zkay.zkay_ast.ast import FunctionDefinition, VariableDeclarationStatement, IfStatement, \
    Block, ExpressionStatement, MeExpr, AssignmentStatement, RequireStatement, AllExpr, ReturnStatement, \
    ConstructorDefinition, FunctionCallExpr, BuiltinFunction, ConstructorOrFunctionDefinition, StatementList
from zkay.zkay_ast.visitor.visitor import AstVisitor


def alias_analysis(ast):
    v = AliasAnalysisVisitor()
    v.visit(ast)


class AliasAnalysisVisitor(AstVisitor):

    def __init__(self, log=False):
        super().__init__('node-or-children', log)

    def handle_function_definition(self, ast: ConstructorOrFunctionDefinition):
        s = PartitionState()
        s.insert(MeExpr().privacy_annotation_label())
        s.insert(AllExpr().privacy_annotation_label())
        for d in ast.parent.state_variable_declarations:
            s.insert(d.idf)
        for p in ast.parameters:
            s.insert(p.idf)
        ast.body.before_analysis = s
        return self.visit(ast.body)

    def visitFunctionDefinition(self, ast: FunctionDefinition):
        return self.handle_function_definition(ast)

    def visitConstructorDefinition(self, ast: ConstructorDefinition):
        return self.handle_function_definition(ast)

    def visitStatementList(self, ast: StatementList):
        return self.visitChildren(ast)

    def visitBlock(self, ast: Block):
        last = ast.before_analysis.copy()

        # add fresh names from this block
        for name in ast.names.values():
            last.insert(name)

        # push state through each statement
        for statement in ast.statements:
            statement.before_analysis = last
            # print('before', statement, last)
            self.visit(statement)
            last = statement.after_analysis
        # print('after', statement, last)

        # remove names falling out of scope
        ast.after_analysis = last.copy()
        for name in ast.names.values():
            ast.after_analysis.remove(name)

    def visitIfStatement(self, ast: IfStatement):
        if has_side_effects(ast.condition):
            ast.before_analysis = ast.before_analysis.separate_all()
        before = ast.before_analysis

        # condition
        self.visit(ast.condition)

        # then
        ast.then_branch.before_analysis = before
        self.visit(ast.then_branch)

        # else
        if ast.else_branch:
            ast.else_branch.before_analysis = before
            self.visit(ast.else_branch)

        # imprecise join (relation between the branches is unclear, so we are conservative)
        ast.after_analysis = before.separate_all()

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
        if has_side_effects(ast):
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
        lhs = lhs.privacy_annotation_label()
        rhs = rhs.privacy_annotation_label()
        if lhs and rhs:
            after.move_to(lhs, rhs)

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
