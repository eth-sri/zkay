from typing import List, TypeVar

from zkay.zkay_ast.ast import AST

T = TypeVar('T')

class AstTransformerVisitor:
    """
    Visitor which replaces visited AST elements by the corresponding visit functions return value

    The default action when no matching visit function is defined, is to replace the node with itself and to visit
    the children. If a matching visit function is defined, children are not automatically visited.
    (Corresponds to node-or-children traversal order from AstVisitor)
    """

    def __init__(self, log=False):
        self.log = log

    def visit(self, ast):
        return self._visit_internal(ast)

    def visit_list(self, ast_list: List[AST]):
        return list(filter(None.__ne__, map(self.visit, ast_list)))

    def visit_children(self, ast: T) -> T:
        ast.process_children(self.visit)
        return ast

    def _visit_internal(self, ast):
        if ast is None:
            return None

        if self.log:
            print('Visiting', type(ast))
        return self.get_visit_function(ast.__class__)(ast)

    def get_visit_function(self, c):
        visitor_function = 'visit' + c.__name__
        if hasattr(self, visitor_function):
            return getattr(self, visitor_function)
        else:
            for base in c.__bases__:
                f = self.get_visit_function(base)
                if f:
                    return f
        assert False

    def visitAST(self, ast: AST):
        return self.visit_children(ast)
