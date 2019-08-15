import os
import re
from typing import List, Tuple

from antlr4 import FileStream


examples_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.join(examples_dir, 'code')
type_error_dir = os.path.join(examples_dir, 'type_errors')
others_dir = os.path.join(examples_dir, 'others')


class Example:

	def __init__(self, file_location: str):
		self.file_location = file_location
		_, self.filename = os.path.split(file_location)

	def code(self):
		with open(self.file_location, 'r') as file:
			return file.read()

	def stream(self):
		return FileStream(self.file_location)

	def name(self):
		c = self.code()
		m = re.search('contract ([^ {]*)', c)
		return m.group(1)

	def normalized(self):
		if self.name() == 'Empty':
			return empty_normalized
		elif self.name() == 'SimpleStorage':
			return simple_storage_normalized
		else:
			return None


simple_storage = Example(os.path.join(code_dir, 'SimpleStorage.sol'))
functions = Example(os.path.join(code_dir, 'Functions.sol'))
addition = Example(os.path.join(code_dir, 'Addition.sol'))
empty = Example(os.path.join(code_dir, 'Empty.sol'))
simple = Example(os.path.join(code_dir, 'Simple.sol'))
control_flow = Example(os.path.join(code_dir, 'ControlFlow.sol'))
analysis = Example(os.path.join(code_dir, 'Analysis.sol'))
private_addition = Example(os.path.join(code_dir, 'PrivateAddition.sol'))
power_grid = Example(os.path.join(code_dir, 'PowerGrid.sol'))
final_use_before_write = Example(os.path.join(others_dir, 'FinalUseBeforeWrite.sol'))
add_user = Example(os.path.join(others_dir, 'AddUser.sol'))


empty_normalized = 'pragma solidity ^ 0.5.0 ; contract Empty { } '
simple_storage_normalized = 'pragma solidity ^ 0.5.0 ; contract SimpleStorage { ' \
	'uint @ all storedData ; ' \
	'function set ( uint @ all x ) public { storedData = x ; } ' \
	'function get ( ) public returns ( uint @ all ) { return storedData ; } } '


def collect_examples(directory: str):
	examples: List[Tuple[str, Example]] = []
	for f in os.listdir(directory):
		if f.endswith(".sol"):
			e = Example(os.path.join(directory, f))
			examples.append((e.name(), e))
	return examples


all_examples = collect_examples(code_dir)
type_error_examples = collect_examples(type_error_dir)
