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
            ast.statement.function.called_functions.add(fdef)
        self.visitChildren(ast)


class IndirectCalledFunctionDetector(FunctionVisitor):
    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        # Fixed point iteration
        size = len(ast.called_functions)
        while True:
            for fct in ast.called_functions:
                ast.called_functions.update(fct.called_functions)

            new_size = len(ast.called_functions)
            if new_size == size:
                break
            size = new_size

        if ast in ast.called_functions:
            # This is a recursive function
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
