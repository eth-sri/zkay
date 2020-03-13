from zkay.zkay_ast.ast import AST, Expression, Statement, ConstructorOrFunctionDefinition, SourceUnit, NamespaceDefinition, Identifier
from zkay.zkay_ast.visitor.visitor import AstVisitor


class ParentSetterVisitor(AstVisitor):
    """
    Links parents
    """

    def __init__(self):
        super().__init__(traversal='pre')

    def visitSourceUnit(self, ast: SourceUnit):
        ast.namespace = []

    def visitNamespaceDefinition(self, ast: NamespaceDefinition):
        ast.namespace = ([] if ast.parent is None else ast.parent.namespace) + [ast.idf]

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        ast.namespace = ([] if ast.parent is None else ast.parent.namespace) + [ast.idf]

    def visitChildren(self, ast: AST):
        for c in ast.children():
            if c is None:
                print(c, ast, ast.children())
            c.parent = ast
            c.namespace = ast.namespace
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
        while parent and not isinstance(parent, ConstructorOrFunctionDefinition):
            parent = parent.parent
        if parent:
            ast.function = parent


def set_parents(ast):
    v = ParentSetterVisitor()
    v.visit(ast)
    v = ExpressionToStatementVisitor()
    v.visit(ast)
