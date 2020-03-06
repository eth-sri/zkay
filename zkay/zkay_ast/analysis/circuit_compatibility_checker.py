from typing import Union

from zkay.config import cfg
from zkay.type_check.type_exceptions import TypeException
from zkay.zkay_ast.ast import ConstructorOrFunctionDefinition, FunctionCallExpr, BuiltinFunction, LocationExpr, \
    Statement, AssignmentStatement, ReturnStatement, ReclassifyExpr, StatementList, Expression, FunctionTypeName, IfStatement, \
    NumberLiteralType, BooleanLiteralType, PrimitiveCastExpr, AST, IndexExpr
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

    check_for_nonstatic_function_calls_or_not_circuit_inlineable_in_private_exprs(ast)


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


class CircuitComplianceChecker(FunctionVisitor):
    def __init__(self):
        super().__init__()
        self.priv_setter = PrivateSetter()
        self.inside_privif_stmt = False

    @staticmethod
    def should_evaluate_public_expr_in_circuit(expr: Expression) -> bool:
        assert expr.annotated_type is not None
        if cfg.opt_eval_constexpr_in_circuit:
            if isinstance(expr.annotated_type.type_name, (NumberLiteralType, BooleanLiteralType)):
                # Expressions for which the value is known at compile time -> embed constant expression value into the circuit
                return True

            if isinstance(expr, PrimitiveCastExpr) and isinstance(expr.expr.annotated_type.type_name, (NumberLiteralType, BooleanLiteralType)):
                # Constant casts should also be evaluated inside the circuit
                return True

        try:
            check_for_nonstatic_function_calls_or_not_circuit_inlineable_in_private_exprs(expr)
        except TypeException:
            # Cannot evaluate inside circuit -> never do it
            return False

        # Could evaluate in circuit, use analysis to determine whether this would be better performance wise
        # (If this avoids unnecessary encryption operations it may be cheaper)
        return False

    def visitIndexExpr(self, ast: IndexExpr):
        if ast.evaluate_privately:
            assert ast.key.annotated_type.is_public()
            self.priv_setter.set_evaluation(ast.key, False)
        return self.visitChildren(ast)

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        if self.inside_privif_stmt and not ast.statement.before_analysis.same_partition(ast.privacy.privacy_annotation_label(), Expression.me_expr()):
            raise TypeException('Revealing information to other parties is not allowed inside private if statements', ast)

        if ast.expr.annotated_type.is_public():
            eval_in_public = False
            try:
                self.priv_setter.set_evaluation(ast, evaluate_privately=True)
            except TypeException:
                eval_in_public = True
            if eval_in_public or not self.should_evaluate_public_expr_in_circuit(ast.expr):
                self.priv_setter.set_evaluation(ast.expr, evaluate_privately=False)
        else:
            self.priv_setter.set_evaluation(ast, evaluate_privately=True)
        self.visit(ast.expr)

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction) and ast.func.is_private:
            self.priv_setter.set_evaluation(ast, evaluate_privately=True)
        elif ast.is_cast and ast.annotated_type.is_private():
            self.priv_setter.set_evaluation(ast, evaluate_privately=True)
        self.visitChildren(ast)

    def visitPrimitiveCastExpr(self, ast: PrimitiveCastExpr):
        if ast.expr.annotated_type.is_private():
            self.priv_setter.set_evaluation(ast, evaluate_privately=True)
        self.visitChildren(ast)

    def visitIfStatement(self, ast: IfStatement):
        old_in_privif_stmt = self.inside_privif_stmt
        if ast.condition.annotated_type.is_private():
            mod_vals = set(ast.then_branch.modified_values.keys())
            if ast.else_branch is not None:
                mod_vals = mod_vals.union(ast.else_branch.modified_values)
            for val in mod_vals:
                if not val.target.annotated_type.zkay_type.type_name.is_primitive_type():
                    raise TypeException('Writes to non-primitive type variables are not allowed inside private if statements', ast)
                if val.in_scope_at(ast) and not ast.before_analysis.same_partition(val.privacy, Expression.me_expr()):
                    raise TypeException('If statement with private condition must not contain side effects to variables with owner != me', ast)
            self.inside_privif_stmt = True
            self.priv_setter.set_evaluation(ast, evaluate_privately=True)
        self.visitChildren(ast)
        self.inside_privif_stmt = old_in_privif_stmt


class PrivateSetter(FunctionVisitor):
    def __init__(self):
        super().__init__()
        self.evaluate_privately = None

    def set_evaluation(self, ast: Union[Expression, Statement], evaluate_privately: bool):
        self.evaluate_privately = evaluate_privately
        self.visit(ast)
        self.evaluate_privately = None

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if self.evaluate_privately and isinstance(ast.func, LocationExpr) and not ast.is_cast and ast.func.target.has_side_effects:
            raise TypeException('Expressions with side effects are not allowed inside private expressions', ast)
        self.visitExpression(ast)

    def visitExpression(self, ast: Expression):
        assert self.evaluate_privately is not None
        ast.evaluate_privately = self.evaluate_privately
        self.visitChildren(ast)


def check_for_nonstatic_function_calls_or_not_circuit_inlineable_in_private_exprs(ast: AST):
    NonstaticOrIncompatibilityDetector().visit(ast)


class NonstaticOrIncompatibilityDetector(FunctionVisitor):
    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        can_be_private = True
        has_nonstatic_call = False
        if ast.evaluate_privately and not ast.is_cast:
            if isinstance(ast.func, LocationExpr):
                assert ast.func.target is not None
                assert isinstance(ast.func.target.annotated_type.type_name, FunctionTypeName)
                has_nonstatic_call |= not ast.func.target.has_static_body
                can_be_private &= ast.func.target.can_be_private
            elif isinstance(ast.func, BuiltinFunction):
                can_be_private &= (ast.func.can_be_private() or ast.annotated_type.type_name.is_literal)
                if ast.func.is_eq() or ast.func.is_ite():
                    can_be_private &= ast.args[1].annotated_type.type_name.can_be_private()
        if has_nonstatic_call:
            raise TypeException('Function calls to non static functions are not allowed inside private expressions', ast)
        if not can_be_private:
            raise TypeException(
                'Calls to functions with operations which cannot be expressed as a circuit are not allowed inside private expressions', ast)
        self.visitChildren(ast)
