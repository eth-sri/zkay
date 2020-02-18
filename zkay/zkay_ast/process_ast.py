from typing import Tuple

from zkay.compiler.solidity.compiler import check_for_zkay_solc_errors, SolcException
from zkay.errors.exceptions import ZkayCompilerError, ParseExeception, PreprocessAstException, TypeCheckException
from zkay.type_check.type_checker import type_check as t
from zkay.type_check.type_exceptions import TypeMismatchException, TypeException, RequireException, ReclassifyException
from zkay.utils.progress_printer import print_step
from zkay.zkay_ast.analysis.alias_analysis import alias_analysis as a
from zkay.zkay_ast.analysis.call_graph import call_graph_analysis
from zkay.zkay_ast.analysis.circuit_compatibility_checker import check_circuit_compliance
from zkay.zkay_ast.analysis.hybrid_function_detector import detect_hybrid_functions
from zkay.zkay_ast.analysis.loop_checker import check_loops
from zkay.zkay_ast.analysis.side_effects import compute_modified_sets, check_for_undefined_behavior_due_to_eval_order
from zkay.zkay_ast.ast import AST
from zkay.zkay_ast.build_ast import build_ast
from zkay.zkay_ast.pointers.parent_setter import set_parents
from zkay.zkay_ast.pointers.pointer_exceptions import UnknownIdentifierException
from zkay.zkay_ast.pointers.symbol_table import link_identifiers as link
from zkay.zkay_ast.analysis.return_checker import check_return as r


def get_parsed_ast_and_fake_code(code, solc_check=True) -> Tuple[AST, str]:
    with print_step("Parsing"):
        from zkay.solidity_parser.parse import SyntaxException
        try:
            ast = build_ast(code)
        except SyntaxException as e:
            raise ParseExeception(f'\n\nPARSER ERROR: {e}')

    from zkay.compiler.solidity.fake_solidity_generator import fake_solidity_code
    fake_code = fake_solidity_code(str(code))
    if solc_check:
        # Solc type checking
        with print_step("Type checking with solc"):
            try:
                check_for_zkay_solc_errors(code, fake_code)
            except SolcException as e:
                raise ZkayCompilerError(f'{e}')
    return ast, fake_code


def get_processed_ast(code, parents=True, link_identifiers=True, check_return=True, alias_analysis=True, type_check=True, solc_check=True) -> AST:
    ast, _ = get_parsed_ast_and_fake_code(code, solc_check=solc_check)

    # Zkay preprocessing and type checking
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
                raise PreprocessAstException(f'\n\nSYMBOL ERROR: {e}')
        if check_return:
            r(ast)
        if alias_analysis:
            a(ast)
        call_graph_analysis(ast)
        compute_modified_sets(ast)
    if type_check:
        with print_step("Zkay type checking"):
            try:
                check_for_undefined_behavior_due_to_eval_order(ast)
                t(ast)
                check_circuit_compliance(ast)
                detect_hybrid_functions(ast)
                check_loops(ast)
            except (TypeMismatchException, TypeException, RequireException, ReclassifyException) as e:
                raise TypeCheckException(f'\n\nCOMPILER ERROR: {e}')
