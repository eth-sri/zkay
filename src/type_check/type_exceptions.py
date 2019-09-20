from zkay_ast.ast import AstException


class TypeException(AstException):
	"""
	Generic exception for type errors in the program
	"""

	pass


class TypeMismatchException(TypeException):

	def __init__(self, expected, actual, ast):
		super().__init__(f'Expected type {str(expected)} but got {str(actual)}', ast)


class RequireException(TypeException):
	"""
	Raised on invalid number of arguments for "require"
	"""
	pass


class ReclassifyException(Exception):
	"""
	Raised on invalid number of arguments for "reveal"
	"""
	pass
