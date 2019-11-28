from typing import Optional

from zkay.zkay_ast.ast import Expression, AST
from zkay.zkay_ast.visitor.visitor import AstVisitor


def contains_private_expr(ast: Optional[AST]):
    if ast is None:
        return False
    v = ContainsPrivVisitor()
    v.visit(ast)
    return v.contains_private


class ContainsPrivVisitor(AstVisitor):
    def __init__(self):
        super().__init__('node-or-children')
        self.contains_private = False

    def visitExpression(self, ast: Expression):
        if ast.is_private:
            self.contains_private = True
            return
        else:
            self.visitChildren(ast)

    def visitAST(self, ast):
        return self.visitChildren(ast)
