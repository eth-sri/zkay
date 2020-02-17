import json
import os
import pathlib
import tempfile
# get relevant paths
from typing import Optional, Dict, Tuple

from solcx import compile_standard
from solcx.exceptions import SolcError

from zkay.config import debug_print, cfg
from zkay.zkay_ast.ast import get_code_error_msg


class SolcException(Exception):
    """ Solc reported error """
    pass


def compile_solidity_json(sol_filename: str, libs: Optional[Dict[str, str]] = None, optimizer_runs: int = -1,
                          output_selection: Tuple = ('metadata', 'evm.bytecode', 'evm.deployedBytecode'),
                          output_dir: str = None) -> Dict:
    """
    Compile the given solidity file using solc json interface with the provided options.

    :param sol_filename: path to solidity file
    :param libs: [OPTIONAL] dictionary containing <LibraryContractName, LibraryContractAddress> pairs, used for linking
    :param optimizer_runs: controls the optimize-runs flag, negative values disable the optimizer
    :param output_selection: determines which fields are included in the compiler output dict
    :param output_dir: compiler output directory
    :return: dictionary with the compilation results according to output_selection
    """
    solp = pathlib.Path(sol_filename)
    json_in = {
        'language': 'Solidity',
        'sources': {
            solp.name: {
                'urls': [
                    str(solp.absolute())
                ]
            }
        },
        'settings': {
            'outputSelection': {
                '*': {'*': list(output_selection)}
            },
        }
    }

    if optimizer_runs >= 0:
        json_in['settings']['optimizer'] = {
            'enabled': True,
            'runs': optimizer_runs
        }

    if libs is not None:
        json_in['settings']['libraries'] = {
            solp.name: libs
        }

    cwd = os.getcwd()
    os.chdir(solp.absolute().parent)
    ret = compile_standard(json_in, allow_paths='.', output_dir=output_dir)
    os.chdir(cwd)
    return ret


def _get_line_col(code: str, idx: int):
    """ Get line and column (1-based) from character index """
    line = len(code[:idx + 1].splitlines())
    col = (idx - (code[:idx + 1].rfind('\n') + 1))
    return line, col


def get_error_order_key(error):
    if 'sourceLocation' in error:
        return error['sourceLocation']['start']
    else:
        return -1


def check_compilation(filename: str, show_errors: bool = False, display_code: str = None):
    """
    Run the given file through solc without output to check for compiler errors.

    :param filename: file to dry-compile
    :param show_errors: if true, errors and warnings are printed
    :param display_code: code to use when displaying the compiler errors
    :raise SolcException: raised if solc reports a compiler error
    """
    sol_name = pathlib.Path(filename).name
    with open(filename) as f:
        code = f.read()
    display_code = code if display_code is None else display_code

    had_error = False
    try:
        errors = compile_solidity_json(filename, None, -1, ())
        if not show_errors:
            return
    except SolcError as e:
        errors = json.loads(e.stdout_data)
        if not show_errors:
            raise SolcException()

    # if solc reported any errors or warnings, print them and throw exception
    if 'errors' in errors:
        debug_print('')
        errors = sorted(errors['errors'], key=get_error_order_key)

        fatal_error_report = ''
        for error in errors:
            from zkay.utils.progress_printer import colored_print, TermColor
            is_error = error['severity'] == 'error'

            with colored_print(TermColor.FAIL if is_error else TermColor.WARNING):
                if 'sourceLocation' in error:
                    file = error['sourceLocation']['file']
                    if file == sol_name:
                        line, column = _get_line_col(code, error['sourceLocation']['start'])
                        report = f'{get_code_error_msg(line, column + 1, str(display_code).splitlines())}\n'
                        had_error |= is_error
                    else:
                        report = f"In imported file '{file}' idx: {error['sourceLocation']['start']}\n"
                report = f'\n{error["severity"].upper()}: {error["type"] if is_error else ""}\n{report}\n{error["message"]}'

                if is_error:
                    fatal_error_report += report
                else:
                    debug_print(report)

        debug_print('')
        if had_error:
            raise SolcException(fatal_error_report)


def check_for_zkay_solc_errors(zkay_code: str, fake_solidity_code: str):
    """
    Run fake solidity code (stripped privacy features) through solc and report errors in the context of the original zkay code.

    Fake solidity code = zkay code with privacy features removed in a source-location preserving way (whitespace padding)

    :param zkay_code: Original zkay code
    :param fake_solidity_code: Corresponding "fake solidity code"
    """

    # dump fake solidity code into temporary file
    with tempfile.NamedTemporaryFile('w', suffix='.sol') as f:
        f.write(fake_solidity_code)
        f.flush()
        check_compilation(f.name, True, display_code=zkay_code)


def compile_solidity_code(code: str, output_directory: str, optimizer_runs=cfg.opt_solc_optimizer_runs) -> Dict:
    """
    Compile the given solidity code with default settings.

    :param code: code to compile
    :param output_directory: compiler output directory
    :param optimizer_runs: solc optimizer argument "runs", a negative value disables the optimizer
    :return: json compilation output
    """

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with tempfile.NamedTemporaryFile('w', suffix='.sol') as f:
        f.write(code)
        f.flush()
        return compile_solidity_json(f.name, output_dir=output_directory, optimizer_runs=optimizer_runs)
