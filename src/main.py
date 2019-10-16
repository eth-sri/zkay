import argparse
import os
import re
from pathlib import Path

import my_logging
from compiler.privacy.zkay_compiler import compile_zkay
from compiler.solidity.compiler import SolcException
from my_logging.log_context import log_context
from utils.helpers import read_file, lines_of_code
from utils.progress_printer import print_step, TermColor, colored_print
from utils.timer import time_measure
from zkay_ast.process_ast import get_processed_ast, TypeCheckException, PreprocessAstException, ParseExeception
from zkay_ast.visitor.statement_counter import count_statements


def parse_arguments():
    # prepare parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--type-check', action='store_true', help="Only type-check, do not compile.")
    msg = 'The directory to output the compiled contract to. Default: Current directory'
    parser.add_argument('--output', default=os.getcwd(), help=msg)
    parser.add_argument(
        '--count-statements',
        default=False,
        action='store_true',
        dest='count',
        help="Count the number of statements in the translated program")
    parser.add_argument('input', type=str, help='The source file')

    # parse
    a = parser.parse_args()

    return a


def compile(file_location: str, d, count, get_binaries=False):
    code = read_file(file_location)

    # log specific features of compiled program
    my_logging.data('originalLoc', lines_of_code(code))
    m = re.search(r'\/\/ Description: (.*)', code)
    if m:
        my_logging.data('description', m.group(1))
    m = re.search(r'\/\/ Domain: (.*)', code)
    if m:
        my_logging.data('domain', m.group(1))
    _, filename = os.path.split(file_location)

    # compile
    with time_measure('compileFull'):
        try:
            ast = get_processed_ast(code)
        except (ParseExeception, PreprocessAstException, TypeCheckException, SolcException):
            exit(3)

        with print_step('Generating solidity code'):
            compile_zkay(ast, d, filename)

        #if get_binaries:
            # compilation of the solidity code is not required
        #    with print_step("Compiling"):
        #        compile_solidity(d, code_file)

    if count:
        my_logging.data('nStatements', count_statements(ast))


if __name__ == '__main__':
    # parse arguments
    a = parse_arguments()

    input_file = Path(a.input)
    if not input_file.exists():
        with colored_print(TermColor.FAIL):
            print(f'Error: input file \'{input_file}\' does not exist')
        exit(1)

    # create output directory
    output_dir = Path(a.output)
    if not output_dir.exists():
        os.mkdir(output_dir)
    elif not output_dir.is_dir():
        with colored_print(TermColor.FAIL):
            print(f'Error: \'{output_dir}\' is not a directory')
        exit(2)

    # create log directory
    log_file = my_logging.get_log_file(filename='compile', parent_dir=str(output_dir), include_timestamp=False, label=None)
    my_logging.prepare_logger(log_file)

    # only type-check
    print(f'Processing file {input_file.name}:')

    if a.type_check:
        code = read_file(str(input_file))

        try:
            ast = get_processed_ast(code)
        except (ParseExeception, PreprocessAstException, TypeCheckException, SolcException):
            exit(3)
    else:
        # compile
        with log_context('inputfile', os.path.basename(a.input)):
            compile(str(input_file), str(output_dir), a.count)

    with colored_print(TermColor.OKGREEN):
        print("Finished successfully")
