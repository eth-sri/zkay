from zkay_ast.ast import AST, Expression, Statement, FunctionDefinition, ConstructorDefinition
from zkay_ast.visitor.visitor import AstVisitor


class ParentSetterVisitor(AstVisitor):
    """
    Links parents
    """

    def visitChildren(self, ast: AST):
        for c in ast.children():
            if c is None:
                print(c, ast, ast.children())
            c.parent = ast
            self.visit(c)


class ExpressionToStatementVisitor(AstVisitor):

    def visitExpression(self, ast: Expression):
        parent = ast
        while parent and not isinstance(parent, Statement):
            parent = parent.parent
        if parent:
            ast.statement = parent

    def visitStatement(self, ast: Statement):
        parent = ast
        while parent and not isinstance(parent, FunctionDefinition) and not isinstance(parent, ConstructorDefinition):
            parent = parent.parent
        if parent:
            ast.function = parent


def set_parents(ast):
    v = ParentSetterVisitor()
    v.visit(ast)
    v = ExpressionToStatementVisitor()
    v.visit(ast)
