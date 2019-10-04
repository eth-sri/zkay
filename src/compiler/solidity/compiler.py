import os
import tempfile
import pathlib
import json
from zkay_ast.ast import get_code_error_msg

# get relevant paths
from utils.run_command import run_command

# could also be 'solc'
solc = 'solcjs'


def create_input_json(uri: str):
	"""
	Generate json input adhering to solc standard-json interface

	:param uri: path to solidity code file (path for solc, uri for solcjs)
	"""
	input_obj = {
			"language": 'Solidity',
			"sources": {
				"contract.sol": {
					"urls": [
						uri
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
	line = len(code[:idx+1].splitlines())
	col = (idx - (code[:idx+1].rfind('\n') + 1))
	return line, col


def check_solc_errors(code: str):
	# dump fake solidity code into temporary file
	_, file = tempfile.mkstemp('.sol')
	path = pathlib.Path(file)
	with open(path, 'w') as f:
		f.write(code)

	# invoke solc via standard-json interface and parse json result
	compiler_input = create_input_json(str(path))
	from subprocess import run, PIPE
	p = run(['solc', '--allow-paths', str(path.absolute().parent), '--standard-json'], stdout=PIPE,
			input=compiler_input, encoding='utf-8')
	json_output = json.loads(p.stdout)
	os.remove(str(path))

	# if solc reported any errors or warnings, print them and throw exception
	if 'errors' in json_output.keys():
		for error in json_output['errors']:
			from utils.progress_printer import colored_print, TermColor
			with colored_print(TermColor.FAIL if error['severity'] == 'error' else TermColor.WARNING):
				if 'sourceLocation' in error:
					line, column = get_line_col(code, error['sourceLocation']['start'])
					report = f'{get_code_error_msg(line, column + 1, str(code).splitlines())}\n'
				else:
					report = ''
				report += error['message']

				print(f'\n\n{error["severity"].upper()}: {error["type"]}')
				print(f'{report}\n')

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
	return run_command([solc, '--bin', '--overwrite',  '-o', output_directory, source_file], path)
