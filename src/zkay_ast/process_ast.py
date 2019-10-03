from utils.progress_printer import print_step, colored_print, TermColor
from zkay_ast.analysis.alias_analysis import alias_analysis as a
from zkay_ast.build_ast import build_ast
from zkay_ast.pointers.parent_setter import set_parents
from zkay_ast.pointers.pointer_exceptions import UnknownIdentifierException
from zkay_ast.pointers.symbol_table import link_identifiers as link
from zkay_ast.visitor.return_checker import check_return as r
from type_check.type_checker import type_check as t

from type_check.type_exceptions import TypeMismatchException, TypeException, RequireException, ReclassifyException


class ParseExeception(Exception):
	"""
	Error during parsing"
	"""
	pass


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
		from solidity_parser.parse import SyntaxException
		try:
			ast = build_ast(code)
		except SyntaxException as e:
			with colored_print(TermColor.FAIL):
				print("\n\nERROR: Syntax error")
				print(f'{str(e)}\n')
			raise ParseExeception()

	from compiler.solidity.fake_solidity_compiler import fake_solidity_code
	fake_code = fake_solidity_code(str(code))
	# TODO create json solc input, invoke solc, read and display errors from json solc output

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
				with colored_print(TermColor.FAIL):
					print("\n\nERROR: Preprocessing failed")
					print(f'{str(e)}\n')
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
				with colored_print(TermColor.FAIL):
					print("\n\nERROR: Type check failed")
					print(f'{str(te)}\n')
				raise TypeCheckException()
