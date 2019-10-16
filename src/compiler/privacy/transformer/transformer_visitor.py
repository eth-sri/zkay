from typing import List

from zkay_ast.ast import AST


class AstTransformerVisitor:
    def __init__(self, log=False):
        self.log = log

    def visit(self, ast):
        return self._visit_internal(ast)

    def visit_list(self, ast_list: List[AST]):
        return list(map(self.visit, ast_list))

    def visit_children(self, ast: AST):
        ast.process_children(self.visit)

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
        self.visit_children(ast)
        return ast
