from zkay.zkay_ast.ast import AnnotatedTypeName, AST
from zkay.zkay_ast.visitor.visitor import AstVisitor


def contains_private(ast):
    v = ContainsPrivateVisitor()
    v.visit(ast)
    return v.contains_private


class ContainsPrivateVisitor(AstVisitor):

    def __init__(self):
        super().__init__()
        self.contains_private = False

    def visitAST(self, ast: AST):
        if hasattr(ast, 'annotated_type'):
            t = ast.annotated_type
            if t is not None:
                assert (isinstance(t, AnnotatedTypeName))

                if not t.privacy_annotation.is_all_expr():
                    self.contains_private = True
