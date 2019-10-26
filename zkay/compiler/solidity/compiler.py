import json
import os
import pathlib
import tempfile

# get relevant paths
from zkay.utils.run_command import run_command
from zkay.zkay_ast.ast import get_code_error_msg

# could also be 'solc'
solc = 'solc'


def create_input_json(sol_file: pathlib.Path):
    """
    Generate json input adhering to solc standard-json interface

    :param uri: path to solidity code file (path for solc, uri for solcjs)
    """
    input_obj = {
        "language": 'Solidity',
        "sources": {
            "contract.sol": {
                "urls": [
                    str(sol_file.absolute())
                ]
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ['']
                }
            }
        }
    }
    return json.dumps(input_obj)


class SolcException(Exception):
    """ Solc reported error """
    pass


def get_line_col(code: str, idx: int):
    """ Get line and column (1-based) from character index """
    line = len(code[:idx + 1].splitlines())
    col = (idx - (code[:idx + 1].rfind('\n') + 1))
    return line, col


def get_error_order_key(error):
    if 'sourceLocation' in error:
        return error['sourceLocation']['start']
    else:
        return -1


def check_solc_errors(original_code: str, stripped_code: str):
    # dump fake solidity code into temporary file
    _, file = tempfile.mkstemp('.sol')
    path = pathlib.Path(file)
    with open(path, 'w') as f:
        f.write(stripped_code)

    # invoke solc via standard-json interface and parse json result
    compiler_input = create_input_json(path)
    from subprocess import run, PIPE
    p = run([solc, '--allow-paths', str(path.absolute().parent), '--standard-json'], stdout=PIPE,
            input=compiler_input, encoding='utf-8')
    json_output = json.loads(p.stdout)
    os.remove(str(path))

    # if solc reported any errors or warnings, print them and throw exception
    if 'errors' in json_output.keys():
        print('')

        had_error = False
        errors = sorted(json_output['errors'], key=get_error_order_key)

        for error in errors:
            from zkay.utils.progress_printer import colored_print, TermColor
            is_error = error['severity'] == 'error'
            had_error = had_error or is_error

            with colored_print(TermColor.FAIL if is_error else TermColor.WARNING):
                if 'sourceLocation' in error:
                    line, column = get_line_col(stripped_code, error['sourceLocation']['start'])
                    report = f'{get_code_error_msg(line, column + 1, str(original_code).splitlines())}\n'
                else:
                    report = ''
                report += error['message']

                print(f'\n{error["severity"].upper()}: {error["type"] if is_error else ""}')
                print(f'{report}')

        print('')
        if had_error:
            raise SolcException()


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
