from zkay.type_check.type_exceptions import TypeException
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


def check_for_side_effects_or_nonstatic_function_calls(ast):
    v = SideEffectsVisitor()
    v.visit(ast)

    if v.has_side_effects:
        raise TypeException('Expressions with side effects are not allowed inside private expressions', ast)
    if v.has_nonstatic_fcall:
        raise TypeException('Function calls to non static functions are not allowed inside private expressions', ast)


class SideEffectsVisitor(AstVisitor):
    """
    No side effects (side-effects by sub-trees are always handled by the visitor):
    - variableDeclarationStatement: only defines a new variable, does not modify an old one
    """

    def __init__(self):
        super().__init__()
        self.has_side_effects = False
        self.has_nonstatic_fcall = False

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            # builtin functions have no side-effects
            pass
        else:
            assert isinstance(ast.func, LocationExpr)
            assert ast.func.target is not None
            assert isinstance(ast.func.target.annotated_type.type_name, FunctionTypeName)
            self.has_nonstatic_fcall = self.has_nonstatic_fcall or not ast.func.target.has_static_body
            self.has_side_effects = self.has_side_effects or ast.func.target.has_side_effects

    def visitAssignmentExpr(self, _):
        self.has_side_effects = True

    def visitAssignmentStatement(self, _):
        self.has_side_effects = True
