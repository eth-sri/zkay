from typing import Set, Dict, Optional

from zkay.type_check.type_exceptions import TypeException
from zkay.zkay_ast.ast import StateVariableDeclaration, \
    AssignmentStatement, IdentifierExpr, ContractDefinition, Block, IfStatement, ConstructorOrFunctionDefinition
from zkay.zkay_ast.visitor.visitor import AstVisitor


def check_final(ast):
    v = FinalVisitor()
    v.visit(ast)


class FinalVisitor(AstVisitor):

    def __init__(self):
        super().__init__('node-or-children')
        self.state_vars_assigned: Optional[Dict[StateVariableDeclaration, bool]] = None

    def visitContractDefinition(self, ast: ContractDefinition):
        self.state_vars_assigned = {}
        for v in ast.state_variable_declarations:
            if v.is_final and v.expr is None:
                self.state_vars_assigned[v] = False

        if len(ast.constructor_definitions) > 0:
            assert (len(ast.constructor_definitions) == 1)
            c = ast.constructor_definitions[0]
            self.visit(c.body)

        for sv, assigned in self.state_vars_assigned.items():
            if not assigned:
                raise TypeException("Did not set all final state variables", sv)

        self.state_vars_assigned = None

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        assert ast.is_function
        return

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        self.visit(ast.rhs)
        if isinstance(ast.lhs, IdentifierExpr):
            var = ast.lhs.target
            if var in self.state_vars_assigned:
                if self.state_vars_assigned[var]:
                    raise TypeException("Tried to reassign final variable", ast)
                self.state_vars_assigned[var] = True

    def visitIfStatement(self, ast: IfStatement):
        self.visit(ast.condition)
        prev = self.state_vars_assigned.copy()
        self.visit(ast.then_branch)
        then_b = self.state_vars_assigned.copy()
        self.state_vars_assigned = prev
        if ast.else_branch is not None:
            self.visit(ast.else_branch)

        assert then_b.keys() == self.state_vars_assigned.keys()
        for var in then_b.keys():
            if then_b[var] != self.state_vars_assigned[var]:
                raise TypeException("Final value is not assigned in both branches", ast)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if ast.is_rvalue() and self.state_vars_assigned is not None:
            if ast.target in self.state_vars_assigned and not self.state_vars_assigned[ast.target]:
                raise TypeException(f'{str(ast)} is reading "final" state variable before writing it', ast)
