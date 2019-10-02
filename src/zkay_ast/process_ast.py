from utils.progress_printer import print_step
from zkay_ast.analysis.alias_analysis import alias_analysis as a
from zkay_ast.build_ast import build_ast
from zkay_ast.pointers.parent_setter import set_parents
from zkay_ast.pointers.pointer_exceptions import UnknownIdentifierException
from zkay_ast.pointers.symbol_table import link_identifiers as link
from zkay_ast.visitor.return_checker import check_return as r
from type_check.type_checker import type_check as t

from type_check.type_exceptions import TypeMismatchException, TypeException, RequireException, ReclassifyException


class PreprocessAstException(Exception):
	"""
	Error during ast preprocessing"
	"""
	pass


class TypeCheckException(Exception):
	"""
	Error during type checking"
	"""
	pass


def get_processed_ast(code, parents=True, link_identifiers=True, check_return=True, alias_analysis=True, type_check=True):
	with print_step("Parsing"):
		ast = build_ast(code)

	process_ast(ast, parents, link_identifiers, check_return, alias_analysis, type_check)
	return ast


def process_ast(ast, parents=True, link_identifiers=True, check_return=True, alias_analysis=True, type_check=True):
	with print_step("Preprocessing AST"):
		if parents:
			set_parents(ast)
		if link_identifiers:
			try:
				link(ast)
			except UnknownIdentifierException as e:
				print("\n\nERROR: Preprocessing failed")
				print(f'{str(e)}')
				raise PreprocessAstException()
		if check_return:
			r(ast)
		if alias_analysis:
			a(ast)
	if type_check:
		with print_step("Type checking"):
			try:
				t(ast)
			except (TypeMismatchException, TypeException, RequireException, ReclassifyException) as te:
				print("\n\nERROR: Type check failed")
				print(f'{str(te)}')
				raise TypeCheckException()
