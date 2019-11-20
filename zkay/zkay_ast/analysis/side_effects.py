from zkay.zkay_ast.ast import FunctionCallExpr, FunctionTypeName, LocationExpr, AssignmentExpr, AssignmentStatement, AST, \
    Expression, Statement
from zkay.zkay_ast.visitor.visitor import AstVisitor


def detect_expressions_with_side_effects(ast) -> bool:
    v = SideEffectsDetector()
    ret = v.visit(ast)
    return ret


class SideEffectsDetector(AstVisitor):
    def visitAssignmentExpr(self, ast: AssignmentExpr):
        ast.has_side_effects = True
        return ast.has_side_effects

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        ast.has_side_effects = self.visitExpression(ast)
        if isinstance(ast.func, LocationExpr):
            assert ast.func.target is not None
            assert isinstance(ast.func.target.annotated_type.type_name, FunctionTypeName)
            ast.has_side_effects |= ast.func.target.has_side_effects
        return ast.has_side_effects

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        ast.has_side_effects = True
        return ast.has_side_effects

    def visitExpression(self, ast: Expression):
        ast.has_side_effects = self.visitAST(ast)
        return ast.has_side_effects

    def visitStatement(self, ast: Statement):
        ast.has_side_effects = self.visitAST(ast)
        return ast.has_side_effects

    def visitAST(self, ast: AST):
        return any(map(self.visit, ast.children()))
