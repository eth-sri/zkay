import os
import shutil
from parameterized import parameterized_class

from compiler.privacy.compiler import compile_code
from compiler.solidity.compiler import compile_solidity
from examples.examples import all_examples
from examples.test_examples import TestExamples


# get relevant paths
script_dir = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(script_dir, 'output')


@parameterized_class(('name', 'example'), all_examples)
class TestCompiler(TestExamples):

    def get_directory(self):
        d = os.path.join(output_dir, self.name)

        if os.path.isdir(d):
            shutil.rmtree(d)
        os.mkdir(d)

        return d

    def test_sanity_checks(self):
        c = self.example.code()
        d = self.get_directory()

        # compile
        code_file = compile_code(c, d, self.example.filename)

        with open(os.path.join(d, code_file), "r") as f:
            code = f.read()

        # check result
        self.assertIsNotNone(code)
        self.assertIn(self.example.name(), code)

    def test_result_compiles(self):
        c = self.example.code()
        d = self.get_directory()

        # compile
        code_file = compile_code(c, d, self.example.filename)

        # with open(os.path.join(d, code_file), "r") as f:
        #     code = f.read()
        #     print(code)

        compile_solidity(d, code_file)
