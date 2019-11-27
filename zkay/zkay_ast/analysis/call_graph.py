from zkay.zkay_ast.ast import ConstructorOrFunctionDefinition, FunctionCallExpr, BuiltinFunction, LocationExpr, \
    FunctionDefinition
from zkay.zkay_ast.visitor.function_visitor import FunctionVisitor


def call_graph_analysis(ast):
    """
    determines (indirectly) called functions for every function
    and concludes from that whether a function has a static body
    """
    v = DirectCalledFunctionDetector()
    v.visit(ast)

    v = IndirectCalledFunctionDetector()
    v.visit(ast)

    v = IndirectDynamicBodyDetector()
    v.visit(ast)


class DirectCalledFunctionDetector(FunctionVisitor):
    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if not isinstance(ast.func, BuiltinFunction):
            assert isinstance(ast.func, LocationExpr)
            fdef = ast.func.target
            assert isinstance(fdef, FunctionDefinition)
            ast.statement.function.called_functions[fdef] = None
        self.visitChildren(ast)


class IndirectCalledFunctionDetector(FunctionVisitor):
    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        # Fixed point iteration
        size = 0
        leaves = ast.called_functions
        while len(ast.called_functions) > size:
            size = len(ast.called_functions)
            leaves = {fct: None for leaf in leaves for fct in leaf.called_functions if fct not in ast.called_functions}
            ast.called_functions.update(leaves)

        if ast in ast.called_functions:
            ast.is_recursive = True
            ast.has_static_body = False


class IndirectDynamicBodyDetector(FunctionVisitor):
    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        if not ast.has_static_body:
            return

        for fct in ast.called_functions:
            if not fct.has_static_body:
                # This function (directly or indirectly) calls a recursive function
                ast.has_static_body = False
                return
