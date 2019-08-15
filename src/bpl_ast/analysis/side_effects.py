from bpl_ast.ast import FunctionCallExpr, BuiltinFunction
from bpl_ast.visitor.visitor import AstVisitor


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

	def visitFunctionCallExpr(self, ast: FunctionCallExpr):
		if isinstance(ast.func, BuiltinFunction):
			# builtin functions have no side-effects
			pass
		else:
			# conservatively assume functions may have side-effects
			self.has_side_effects = True

	def visitAssignmentExpr(self, _):
		self.has_side_effects = True

	def visitAssignmentStatement(self, _):
		self.has_side_effects = True
