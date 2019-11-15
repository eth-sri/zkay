from zkay.zkay_ast.ast import SourceUnit, Parameter
from zkay.zkay_ast.visitor.visitor import AstVisitor


class FunctionVisitor(AstVisitor):
    def __init__(self):
        super().__init__('node-or-children')

    def visitSourceUnit(self, ast: SourceUnit):
        for c in ast.contracts:
            list(map(self.visit, c.constructor_definitions))
            list(map(self.visit, c.function_definitions))

    def visitParameter(self, ast: Parameter):
        pass
