from zkay_ast.ast import AST, Statement
from zkay_ast.visitor.visitor import AstVisitor


def count_statements(ast: AST, log_found=False):
	v = StatementCounter(log_found)
	v.visit(ast)
	return v.count


class StatementCounter(AstVisitor):

	def __init__(self, log_found=False):
		super().__init__()
		self.count = 0
		self.log_found = log_found

	def visitStatement(self, ast: Statement):
		if self.log_found:
			print(f'Counting {ast}')
		self.count += 1

	def visitBlock(self, ast: Statement):
		# do not count blocks
		pass
