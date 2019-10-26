from typing import Set

from zkay.type_check.type_exceptions import TypeException
from zkay.zkay_ast.ast import StateVariableDeclaration, \
    AssignmentStatement, IdentifierExpr, ContractDefinition
from zkay.zkay_ast.visitor.visitor import AstVisitor


def check_final(ast):
    v = FinalVisitor()
    v.visit(ast)


class FinalVisitor(AstVisitor):

    def __init__(self):
        super().__init__('node-or-children')
        self.state_vars: Set[StateVariableDeclaration] = None

    def visitContractDefinition(self, ast: ContractDefinition):
        self.state_vars = set()
        for v in ast.state_variable_declarations:
            if 'final' in v.keywords and v.expr is None:
                self.state_vars.add(v)

        if len(ast.constructor_definitions) > 0:
            assert (len(ast.constructor_definitions) == 1)
            c = ast.constructor_definitions[0]
            for s in c.body:
                if isinstance(s, AssignmentStatement):
                    self.visit(s.rhs)
                    if isinstance(s.lhs, IdentifierExpr):
                        var = s.lhs.target
                        if var in self.state_vars:
                            self.state_vars.remove(var)
                else:
                    self.visit(s)

        if len(self.state_vars) > 0:
            raise TypeException("Did not set all final state variables", ast)

        self.state_vars = None

        self.visitChildren(ast)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if self.state_vars is not None:
            if ast.target in self.state_vars:
                raise TypeException(f'{str(ast)} is reading "final" state variable before writing it', ast)
