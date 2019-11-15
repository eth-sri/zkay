from zkay.type_check.type_exceptions import TypeException
from zkay.zkay_ast.ast import ReclassifyExpr, Expression, ConstructorOrFunctionDefinition, AllExpr, AstException, FunctionCallExpr, \
    LocationExpr
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

    v = NonInlineableCallDetector()
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


class NonInlineableCallDetector(FunctionVisitor):
    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, LocationExpr):
            if ast.func.target.requires_verification and ast.func.target.is_recursive:
                raise TypeException("Non-inlineable call to recursive private function", ast.func)
        self.visitChildren(ast)
