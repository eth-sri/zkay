import os

# get relevant paths
from utils.run_command import run_command

# could also be 'solc'
solc = 'solcjs'


def compile_solidity_code(code: str, output_directory: str):

    source_name = 'code.sol'
    file_path = os.path.join(output_directory, source_name)
    with open(file_path, "w") as f:
        f.write(code)

    return compile_solidity(output_directory, source_name)


def compile_solidity(path: str, source_file: str, output_directory: str = None):
    if not output_directory:
        output_directory = path
    output_directory = os.path.abspath(output_directory)
    return run_command([solc, '--bin', '--overwrite',  '-o', output_directory, source_file], path)
