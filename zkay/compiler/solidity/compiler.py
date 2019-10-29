import json
import os
import pathlib
import tempfile
# get relevant paths
from typing import Optional, Dict, Tuple

from solcx import compile_standard
from solcx.exceptions import SolcError

from zkay.utils.run_command import run_command
from zkay.zkay_ast.ast import get_code_error_msg

# could also be 'solc'
solc = 'solc'


class SolcException(Exception):
    """ Solc reported error """
    pass


def compile_solidity_json(sol_filename: str, libs: Optional[Dict] = None, optimizer_runs: int = -1, output_selection: Tuple = ('metadata', 'evm.bytecode')):
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
    ret = compile_standard(json_in, allow_paths='.')
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


def check_compilation(filename: str, show_errors: bool = False, code: str = None, display_code: str = None):
    sol_name = pathlib.Path(filename).name
    if code is None:
        with open(filename) as f:
            code = f.read()
            display_code = code

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
        print('')
        errors = sorted(errors['errors'], key=get_error_order_key)

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
                report += error['message']

                print(f'\n{error["severity"].upper()}: {error["type"] if is_error else ""}')
                print(f'{report}')

        print('')
        if had_error:
            raise SolcException()


def check_for_zkay_solc_errors(zkay_code: str, fake_solidity_code: str):
    # dump fake solidity code into temporary file
    _, file = tempfile.mkstemp('.sol')
    path = pathlib.Path(file)
    with open(path, 'w') as f:
        f.write(fake_solidity_code)
    check_compilation(file, True, fake_solidity_code, zkay_code)
    os.remove(str(path))


def compile_solidity_code(code: str, output_directory: str):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    source_name = 'code.sol'
    file_path = os.path.join(output_directory, source_name)
    with open(file_path, "w") as f:
        f.write(code)

    return compile_solidity(output_directory, source_name)


def compile_solidity(path: str, source_file: str, output_directory: str = None):
    if not output_directory:
        output_directory = path
    output_directory = os.path.abspath(output_directory)
    return run_command([solc, '--bin', '--overwrite', '-o', output_directory, source_file], path)
