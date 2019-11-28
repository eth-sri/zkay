from typing import List

from zkay.type_check.type_exceptions import TypeException
from zkay.zkay_ast.ast import FunctionCallExpr, FunctionTypeName, LocationExpr, AssignmentExpr, AssignmentStatement, AST, \
    Expression, Statement, IdentifierExpr, MemberAccessExpr, IndexExpr, StateVariableDeclaration, BuiltinFunction
from zkay.zkay_ast.visitor.function_visitor import FunctionVisitor
from zkay.zkay_ast.visitor.visitor import AstVisitor


def detect_expressions_with_side_effects(ast: AST) -> bool:
    v = SideEffectsDetector()
    ret = v.visit(ast)
    return ret


def compute_modified_sets(ast: AST):
    v = DirectModificationDetector()
    v.visit(ast)

    v = IndirectModificationDetector()
    v.iterate_until_fixed_point(ast)


def check_for_undefined_behavior_due_to_eval_order(ast: AST):
    EvalOrderUBChecker().visit(ast)


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


class DirectModificationDetector(FunctionVisitor):
    def visitAssignmentStatement(self, ast: AssignmentStatement):
        return self.visitAssignmentExpr(ast)

    def visitAssignmentExpr(self, ast: AssignmentExpr):
        self.visitAST(ast)
        if isinstance(ast.lhs, IdentifierExpr):
            ast.modified_values.add((ast.lhs.target, None))
        elif isinstance(ast.lhs, MemberAccessExpr):
            ast.modified_values.add((ast.lhs.expr.target, ast.lhs.member.clone()))
        else:
            assert isinstance(ast.lhs, IndexExpr)
            # over approximation (since index can be dynamic)
            ast.modified_values.add((ast.lhs.arr.target, None))

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        ast.read_values.clear()
        if ast.is_rvalue():
            ast.read_values.add((ast.target, None))

    def visitAST(self, ast: AST):
        ast.modified_values.clear()
        ast.read_values.clear()
        for child in ast.children():
            self.visit(child)
            ast.modified_values.update(child.modified_values)
            ast.read_values.update(child.read_values)


class IndirectModificationDetector(FunctionVisitor):
    def __init__(self):
        super().__init__()
        self.fixed_point_reached = True

    def iterate_until_fixed_point(self, ast):
        while True:
            self.visit(ast)
            if self.fixed_point_reached:
                break
            else:
                self.fixed_point_reached = True

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        self.visitAST(ast)
        if isinstance(ast.func, LocationExpr):
            # for now no reference types -> only state could have been modified
            if ast.has_side_effects:
                fdef = ast.func.target
                mlen = len(ast.modified_values)
                rlen = len(ast.read_values)
                ast.modified_values.update({v for v in fdef.modified_values if isinstance(v[0], StateVariableDeclaration)})
                ast.read_values.update({v for v in fdef.read_values if isinstance(v[0], StateVariableDeclaration)})
                self.fixed_point_reached &= mlen == len(ast.modified_values)
                self.fixed_point_reached &= rlen == len(ast.read_values)

    def visitAST(self, ast: AST):
        mlen = len(ast.modified_values)
        rlen = len(ast.read_values)
        for child in ast.children():
            self.visit(child)
            ast.modified_values.update(child.modified_values)
            ast.read_values.update(child.read_values)
        self.fixed_point_reached &= mlen == len(ast.modified_values)
        self.fixed_point_reached &= rlen == len(ast.read_values)


class EvalOrderUBChecker(AstVisitor):
    @staticmethod
    def visit_child_expressions(parent: AST, exprs: List[AST]):
        if len(exprs) > 1:
            modset = exprs[0].modified_values.copy()
            for arg in exprs[1:]:
                diffset = modset.intersection(arg.modified_values)
                if diffset:
                    setstr = f'{{{", ".join(map(str, diffset))}}}'
                    raise TypeException(f'Undefined behavior due to potential side effect on the same value(s) \'{setstr}\' in multiple expression children.\n'
                                        'Solidity does not guarantee an evaluation order for non-shortcircuit expressions.\n'
                                        'Since zkay requires local simulation for transaction transformation, all semantics must be well-defined.', parent)
                else:
                    modset.update(diffset)

            for arg in exprs:
                modset = arg.modified_values.copy()
                other_args = [e for e in exprs if e != arg]
                for arg2 in other_args:
                    diffset = modset.intersection(arg2.read_values)
                    if diffset:
                        setstr = f'{{{", ".join([str(val) + (f".{str(member)}" if member else "") for val, member in diffset])}}}'
                        raise TypeException(
                            f'Undefined behavior due to read of value(s) \'{setstr}\' which might be modified in this subexpression.\n'
                            'Solidity does not guarantee an evaluation order for non-shortcircuit expressions.\n'
                            'Since zkay requires local simulation for transaction transformation, all semantics must be well-defined.', arg)

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            if ast.func.has_shortcircuiting():
                return
        self.visit_child_expressions(ast, ast.args)

    def visitExpression(self, ast: Expression):
        self.visit_child_expressions(ast, ast.children())

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        self.visit_child_expressions(ast, ast.children())
