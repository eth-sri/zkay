from zkay.zkay_ast.ast import FunctionCallExpr, BuiltinFunction, FunctionTypeName, LocationExpr
from zkay.zkay_ast.visitor.visitor import AstVisitor


def has_side_effects(ast):
    """

    :param ast:
    :return: true if ast is guaranteed to have no side-effects
    """
    v = SideEffectsVisitor()
    v.visit(ast)
    return v.has_side_effects


class SideEffectsVisitor(AstVisitor):
    """
    No side effects (side-effects by sub-trees are always handled by the visitor):
    - variableDeclarationStatement: only defines a new variable, does not modify an old one
    """

    def __init__(self):
        super().__init__()
        self.has_side_effects = False
        self.has_nonstatic_fcall = False
        self.can_be_private = True

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            # builtin functions have no side-effects
            pass
        else:
            assert isinstance(ast.func, LocationExpr)
            assert ast.func.target is not None
            assert isinstance(ast.func.target.annotated_type.type_name, FunctionTypeName)
            self.has_side_effects |= ast.func.target.has_side_effects
            self.has_nonstatic_fcall |= not ast.func.target.has_static_body
            self.can_be_private &= ast.func.target.can_be_private

    def visitAssignmentExpr(self, _):
        self.has_side_effects = True
        raise NotImplementedError()

    def visitAssignmentStatement(self, _):
        self.has_side_effects = True
