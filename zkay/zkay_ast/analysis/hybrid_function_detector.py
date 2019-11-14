from zkay.zkay_ast.ast import ReclassifyExpr, Expression, ConstructorOrFunctionDefinition, AllExpr, AstException
from zkay.zkay_ast.visitor.function_visitor import FunctionVisitor


def detect_hybrid_functions(ast):
    """

    :param ast:
    :return: marks all functions which will require verification
    """
    v = DirectHybridFunctionDetectionVisitor()
    v.visit(ast)

    v = IndirectHybridFunctionDetectionVisitor()
    v.visit(ast)


class DirectHybridFunctionDetectionVisitor(FunctionVisitor):
    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        ast.statement.function.requires_verification = True

    def visitAllExpr(self, ast: AllExpr):
        pass

    def visitExpression(self, ast: Expression):
        if ast.annotated_type.is_private():
            ast.statement.function.requires_verification = True

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        for param in ast.parameters:
            if param.annotated_type.is_private():
                ast.requires_verification = True
        self.visit(ast.body)


class IndirectHybridFunctionDetectionVisitor(FunctionVisitor):
    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        if not ast.requires_verification:
            for fct in ast.called_functions:
                if fct.requires_verification:
                    ast.requires_verification = True
                    break
