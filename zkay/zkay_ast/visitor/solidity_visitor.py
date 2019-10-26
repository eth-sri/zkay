from zkay.zkay_ast.ast import MeExpr, AnnotatedTypeName, CodeVisitor, AST


def to_solidity(ast: AST):
    v = SolidityVisitor()
    s = v.visit(ast)
    return s


class SolidityVisitor(CodeVisitor):

    def __init__(self):
        # do not display `final` keywords (`final` is not in Solidity fragment)
        super().__init__(False)

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
        # only display data type, not privacy annotation
        t = self.visit(ast.type_name)
        return t

    def visitMeExpr(self, _: MeExpr):
        return 'msg.sender'
