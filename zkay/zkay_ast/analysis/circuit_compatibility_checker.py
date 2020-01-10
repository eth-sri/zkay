from typing import Union

from zkay.type_check.type_exceptions import TypeException
from zkay.zkay_ast.ast import ConstructorOrFunctionDefinition, FunctionCallExpr, BuiltinFunction, LocationExpr, \
    Statement, AssignmentStatement, ReturnStatement, ReclassifyExpr, StatementList, Expression, FunctionTypeName, NumberLiteralExpr, \
    BooleanLiteralExpr, IfStatement, NumberLiteralType, BooleanLiteralType
from zkay.zkay_ast.visitor.function_visitor import FunctionVisitor


def check_circuit_compliance(ast):
    """
    determines for every function whether it can be used inside a circuit
    """
    v = DirectCanBePrivateDetector()
    v.visit(ast)

    v = IndirectCanBePrivateDetector()
    v.visit(ast)

    v = CircuitComplianceChecker()
    v.visit(ast)


class DirectCanBePrivateDetector(FunctionVisitor):
    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            if not ast.func.is_private:
                can_be_private = ast.func.can_be_private()
                if ast.func.is_eq() or ast.func.is_ite():
                    can_be_private &= ast.args[1].annotated_type.type_name.can_be_private()
                ast.statement.function.can_be_private &= can_be_private
        for arg in ast.args:
            self.visit(arg)

    def visitLocationExpr(self, ast: LocationExpr):
        t = ast.annotated_type.type_name
        ast.statement.function.can_be_private &= (t == t.uint_type() or t == t.bool_type())
        self.visitChildren(ast)

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        return self.visit(ast.expr)

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        self.visitChildren(ast)

    def visitVariableDeclarationStatement(self, ast: AssignmentStatement):
        self.visitChildren(ast)

    def visitReturnStatement(self, ast: ReturnStatement):
        self.visitChildren(ast)

    def visitIfStatement(self, ast: IfStatement):
        self.visitChildren(ast)

    def visitStatementList(self, ast: StatementList):
        self.visitChildren(ast)

    def visitStatement(self, ast: Statement):
        # All other statement types are not supported inside circuit (for now)
        ast.function.can_be_private = False


class IndirectCanBePrivateDetector(FunctionVisitor):
    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        if ast.can_be_private:
            for fct in ast.called_functions:
                if not fct.can_be_private:
                    ast.can_be_private = False
                    return


def check_for_side_effects_nonstatic_function_calls_or_not_circuit_inlineable(ast: Union[Statement, Expression], check_side_effects: bool = True):
    if check_side_effects and ast.has_side_effects:
        raise TypeException('Expressions with side effects are not allowed inside private expressions', ast)

    v = NonstaticOrIncompatibilityDetector()
    v.visit(ast)
    if v.has_nonstatic_fcall:
        raise TypeException('Function calls to non static functions are not allowed inside private expressions', ast)
    if not v.can_be_private:
        raise TypeException('Calls to functions with operations which cannot be expressed as a circuit are not allowed inside private expressions', ast)


class CircuitComplianceChecker(FunctionVisitor):
    def __init__(self):
        super().__init__()
        self.priv_setter = PrivateSetter()

    def should_evaluate_public_expr_in_circuit(self, expr: Expression) -> bool:
        try:
            check_for_side_effects_nonstatic_function_calls_or_not_circuit_inlineable(expr)
        except TypeException:
            # Cannot evaluate inside circuit -> never do it
            return False

        assert expr.annotated_type is not None
        if isinstance(expr.annotated_type.type_name, (NumberLiteralType, BooleanLiteralType)):
            # Expressions for which the value is known at compile time -> embed constant expression value into the circuit
            return True

        # Could evaluate in circuit, use analysis to determine whether this would be better performance wise
        # (If this avoids unnecessary encryption operations it may be cheaper)
        return False

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        ast.evaluate_privately = True
        if ast.expr.annotated_type.is_public() and not self.should_evaluate_public_expr_in_circuit(ast.expr):
            self.priv_setter.set_evaluation(ast.expr, evaluate_privately=False)
        else:
            check_for_side_effects_nonstatic_function_calls_or_not_circuit_inlineable(ast.expr)
            self.priv_setter.set_evaluation(ast.expr, evaluate_privately=True)
        self.visit(ast.expr)

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction) and ast.func.is_private:
            for arg in ast.args:
                check_for_side_effects_nonstatic_function_calls_or_not_circuit_inlineable(arg)
            self.priv_setter.set_evaluation(ast, evaluate_privately=True)
        self.visitChildren(ast)

    def visitIfStatement(self, ast: IfStatement):
        if ast.condition.annotated_type.is_private():
            check_for_side_effects_nonstatic_function_calls_or_not_circuit_inlineable(ast.condition)
            check_for_side_effects_nonstatic_function_calls_or_not_circuit_inlineable(ast.then_branch, check_side_effects=False)
            mod_vals = ast.then_branch.modified_values
            if ast.else_branch is not None:
                check_for_side_effects_nonstatic_function_calls_or_not_circuit_inlineable(ast.else_branch, check_side_effects=False)
                mod_vals = mod_vals.union(ast.else_branch.modified_values)
            for val in mod_vals:
                if val.in_scope_at(ast) and val.target.annotated_type.is_public():
                    raise TypeException('If statement with private condition must not contain side effects to public variables', ast)
            self.priv_setter.set_evaluation(ast, evaluate_privately=True)
        self.visitChildren(ast)


class PrivateSetter(FunctionVisitor):
    def __init__(self):
        super().__init__()
        self.evaluate_privately = None

    def set_evaluation(self, ast: Union[Expression, Statement], evaluate_privately: bool):
        self.evaluate_privately = evaluate_privately
        self.visit(ast)
        self.evaluate_privately = None

    def visitExpression(self, ast: Expression):
        assert self.evaluate_privately is not None
        ast.evaluate_privately = self.evaluate_privately
        self.visitChildren(ast)

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        # this subtree will be set later
        return


class NonstaticOrIncompatibilityDetector(FunctionVisitor):
    def __init__(self):
        super().__init__()
        self.has_nonstatic_fcall = False
        self.can_be_private = True

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, LocationExpr):
            assert ast.func.target is not None
            assert isinstance(ast.func.target.annotated_type.type_name, FunctionTypeName)
            self.has_nonstatic_fcall |= not ast.func.target.has_static_body
            self.can_be_private &= ast.func.target.can_be_private
        elif isinstance(ast.func, BuiltinFunction):
            self.can_be_private &= ast.func.can_be_private()
            if ast.func.is_eq() or ast.func.is_ite():
                self.can_be_private &= ast.args[1].annotated_type.type_name.can_be_private()
        self.visitChildren(ast)

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        # This subtree will be checked later
        return
