from bpl_ast.analysis.alias_analysis import alias_analysis as a
from bpl_ast.build_ast import build_ast
from bpl_ast.pointers.parent_setter import set_parents
from bpl_ast.pointers.symbol_table import link_identifiers as link
from bpl_ast.visitor.return_checker import check_return as r
from type_check.type_checker import type_check as t


def get_processed_ast(code, parents=True, link_identifiers=True, check_return=True, alias_analysis=True, type_check=True):
	ast = build_ast(code)
	process_ast(ast, parents, link_identifiers, check_return, alias_analysis, type_check)
	return ast


def process_ast(ast, parents=True, link_identifiers=True, check_return=True, alias_analysis=True, type_check=True):
	if parents:
		set_parents(ast)
	if link_identifiers:
		link(ast)
	if check_return:
		r(ast)
	if alias_analysis:
		a(ast)
	if type_check:
		t(ast)
