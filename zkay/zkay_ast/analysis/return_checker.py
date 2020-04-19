from zkay.zkay_ast.ast import ReturnStatement, Block, ConstructorOrFunctionDefinition, AstException
from zkay.zkay_ast.visitor.visitor import AstVisitor


def check_return(ast):
    v = ReturnCheckVisitor()
    v.visit(ast)


class ReturnPositionException(AstException):

    def __init__(self, ast: ReturnStatement):
        super().__init__('Return statements are only allowed at the end of a function.', ast)


class ReturnCheckVisitor(AstVisitor):

    def visitReturnStatement(self, ast: ReturnStatement):
        container = ast.parent
        assert isinstance(container, Block)
        ok = True
        if container.statements[-1] != ast:
            ok = False
        if not isinstance(container.parent, ConstructorOrFunctionDefinition) or container.parent.is_constructor:
            ok = False
        if not ok:
            raise ReturnPositionException(ast)
