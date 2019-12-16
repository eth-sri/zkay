from zkay.type_check.type_exceptions import TypeException
from zkay.zkay_ast.analysis.contains_private_checker import contains_private_expr
from zkay.zkay_ast.ast import WhileStatement, ForStatement, DoWhileStatement
from zkay.zkay_ast.visitor.function_visitor import FunctionVisitor


def check_loops(ast):
    """
    Checks if loops don't contain private expressions
    """
    v = LoopChecker()
    v.visit(ast)


class LoopChecker(FunctionVisitor):
    def visitWhileStatement(self, ast: WhileStatement):
        if contains_private_expr(ast.condition):
            raise TypeException('Loop condition cannot contain private expressions', ast.condition)
        if contains_private_expr(ast.body):
            raise TypeException('Loop body cannot contain private expressions', ast.body)
        self.visitChildren(ast)

    def visitDoWhileStatement(self, ast: DoWhileStatement):
        if contains_private_expr(ast.condition):
            raise TypeException('Loop condition cannot contain private expressions', ast.condition)
        if contains_private_expr(ast.body):
            raise TypeException('Loop body cannot contain private expressions', ast.body)
        self.visitChildren(ast)

    def visitForStatement(self, ast: ForStatement):
        if contains_private_expr(ast.condition):
            raise TypeException('Loop condition cannot contain private expressions', ast.condition)
        if contains_private_expr(ast.body):
            raise TypeException('Loop body cannot contain private expressions', ast.body)
        if ast.update is not None and contains_private_expr(ast.update):
            raise TypeException('Loop update expression cannot contain private expressions', ast.update)
        self.visitChildren(ast)
