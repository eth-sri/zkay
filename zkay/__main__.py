import ast
import argparse
import os
from pathlib import Path

from zkay import my_logging
from zkay.compiler.privacy.zkay_frontend import compile_zkay_file
from zkay.config import cfg
from zkay.errors.exceptions import ZkayCompilerError
from zkay.my_logging.log_context import log_context
from zkay.utils.helpers import read_file
from zkay.utils.progress_printer import TermColor, colored_print
from zkay.zkay_ast.process_ast import get_processed_ast, get_parsed_ast_and_fake_code


def parse_arguments():
    # prepare parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-fake-solidity', action='store_true', help='Output fake solidity code (zkay code without privacy features and comments)')
    parser.add_argument('--type-check', action='store_true', help='Only type-check, do not compile.')
    msg = 'The directory to output the compiled contract to. Default: Current directory'
    parser.add_argument('--output', default=os.getcwd(), help=msg)
    parser.add_argument(
        '--count-statements',
        default=False,
        action='store_true',
        dest='count',
        help="Count the number of statements in the translated program")
    parser.add_argument('input', type=str, help='The source file')

    # Expose config.py user options
    for copt in vars(cfg):
        if not copt.startswith('_'):
            parser.add_argument(f'--{copt}', dest=copt, help='see config.py')

    # parse
    a = parser.parse_args()

    return a


if __name__ == '__main__':
    # parse arguments
    a = parse_arguments()

    # Support for overriding any user config setting via command line
    override_dict = {}
    for copt in vars(cfg):
        if hasattr(a, copt) and getattr(a, copt) is not None:
            v = getattr(a, copt).strip()
            try:
                val = ast.literal_eval(v) # Try to interpret type
            except ValueError:
                val = v # It is a string
            override_dict[copt] = val
    cfg.override_defaults(override_dict)

    input_file = Path(a.input)
    if not input_file.exists():
        with colored_print(TermColor.FAIL):
            print(f'Error: input file \'{input_file}\' does not exist')
        exit(1)

    # create output directory
    output_dir = Path(a.output).absolute()
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

    if a.output_fake_solidity:
        _, fake_code = get_parsed_ast_and_fake_code(read_file(str(input_file)))
        with open(os.path.join(output_dir, f'{input_file.name}.fake.sol'), 'w') as f:
            f.write(fake_code)
    elif a.type_check:
        code = read_file(str(input_file))
        try:
            ast = get_processed_ast(code)
        except ZkayCompilerError as e:
            with colored_print(TermColor.FAIL):
                print(f'{e}')
            exit(3)
    else:
        # compile
        with log_context('inputfile', os.path.basename(a.input)):
            try:
                compile_zkay_file(str(input_file), str(output_dir))
            except ZkayCompilerError as e:
                with colored_print(TermColor.FAIL):
                    print(f'{e}')
                exit(3)

    with colored_print(TermColor.OKGREEN):
        print("Finished successfully")
