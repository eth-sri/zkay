class AstVisitor:

    def __init__(self, traversal='post', log=False):
        self.traversal = traversal
        self.log = log

    def visit(self, ast):
        return self._visit_internal(ast)

    def _visit_internal(self, ast):
        if self.log:
            print('Visiting', type(ast))
        ret = None
        ret_children = None

        if self.traversal == 'post':
            ret_children = self.visitChildren(ast)
        f = self.get_visit_function(ast.__class__)
        if f:
            ret = f(ast)
        elif self.traversal == 'node-or-children':
            ret_children = self.visitChildren(ast)
        if self.traversal == 'pre':
            ret_children = self.visitChildren(ast)
        if ret:
            return ret
        elif ret_children:
            return ret_children
        else:
            return None

    def get_visit_function(self, c):
        visitor_function = 'visit' + c.__name__
        if hasattr(self, visitor_function):
            return getattr(self, visitor_function)
        else:
            for base in c.__bases__:
                f = self.get_visit_function(base)
                if f:
                    return f
        return None

    def visitChildren(self, ast):
        for c in ast.children():
            self.visit(c)
