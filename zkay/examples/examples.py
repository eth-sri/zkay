import os
import re
from typing import List, Tuple

from antlr4 import FileStream

from zkay.config import cfg
from zkay.utils.helpers import get_contract_names

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
            return file.read().replace('\t', cfg.indentation)

    def stream(self):
        return FileStream(self.file_location)

    def name(self):
        names = get_contract_names(self.file_location)
        assert len(names) == 1
        return names[0]

    def normalized(self):
        if self.name() == 'Empty':
            return empty_normalized
        elif self.name() == 'SimpleStorage':
            return simple_storage_normalized
        else:
            return None


simple_storage = Example(os.path.join(code_dir, 'SimpleStorage.zkay'))
functions = Example(os.path.join(code_dir, 'Functions.zkay'))
addition = Example(os.path.join(code_dir, 'Addition.zkay'))
empty = Example(os.path.join(code_dir, 'Empty.zkay'))
simple = Example(os.path.join(code_dir, 'Simple.zkay'))
control_flow = Example(os.path.join(code_dir, 'ControlFlow.zkay'))
analysis = Example(os.path.join(code_dir, 'Analysis.zkay'))
private_addition = Example(os.path.join(code_dir, 'PrivateAddition.zkay'))
power_grid = Example(os.path.join(code_dir, 'PowerGrid.zkay'))
final_use_before_write = Example(os.path.join(others_dir, 'FinalUseBeforeWrite.zkay'))
add_user = Example(os.path.join(others_dir, 'AddUser.sol'))

empty_normalized = f'pragma zkay >= {cfg.zkay_version} ; contract Empty {{ }} '
simple_storage_normalized = f'pragma zkay >= {cfg.zkay_version} ; contract SimpleStorage {{ ' \
                            'uint @ all storedData ; ' \
                            'function set ( uint @ all x ) public { storedData = x ; } ' \
                            'function get ( ) public returns ( uint @ all ) { return storedData ; } } '


def collect_examples(directory: str):
    examples: List[Tuple[str, Example]] = []
    for f in os.listdir(directory):
        if f.endswith('.zkay'):
            e = Example(os.path.join(directory, f))
            examples.append((e.name(), e))
    return examples


def get_code_example(name: str):
    e = Example(os.path.join(code_dir, name))
    return [(e.name(), e)]


all_examples = collect_examples(code_dir)
type_error_examples = collect_examples(type_error_dir)
