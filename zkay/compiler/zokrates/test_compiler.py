import os
from unittest import TestCase

from zkay.compiler.solidity.compiler import compile_solidity
from zkay.compiler.zokrates.compiler import compile_zokrates, generate_proof
from zkay.utils.helpers import read_file

script_dir = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(script_dir, 'output')


class TestCompileZokrates(TestCase):

    def test_compile_1(self):
        output_filename, _ = compile_zokrates(example, output_dir, 'ABC')
        verifier_filename = os.path.join(output_dir, output_filename)
        verifier_code = read_file(verifier_filename)

        self.assertIn('contract ABC', verifier_code)

    def test_compile_encryption(self):
        output_filename, _ = compile_zokrates(example_encryption, output_dir, 'DEF')
        verifier_filename = os.path.join(output_dir, output_filename)
        verifier_code = read_file(verifier_filename)

        self.assertIn('contract DEF', verifier_code)

    def test_files_exist(self):
        output_filename, zok_dir = compile_zokrates(example, output_dir, 'HIJ')

        # check output file
        sol = 'HIJ_verifier.sol'
        self.assertEqual(output_filename, sol)

        sol = os.path.join(output_dir, output_dir)
        self.assertTrue(os.path.exists(sol))

        # check output directory
        self.assertTrue(os.path.isdir(zok_dir))
        d = os.path.join(output_dir, 'HIJ_zok')
        self.assertEqual(d, zok_dir)

    def test_compile_2(self):
        output_filename, _ = compile_zokrates(example, output_dir, 'KLM')
        compile_solidity(output_dir, output_filename, output_dir)

    def test_generate_proof(self):
        output_filename, zok_dir = compile_zokrates(example, output_dir, 'NOP')
        proof = generate_proof(zok_dir, [3, 9])
        self.assertIn('input', proof)

    def test_generate_invalid_proof(self):
        output_filename, zok_dir = compile_zokrates(example, output_dir, 'QRS')
        with self.assertRaises(ValueError):
            generate_proof(zok_dir, [3, 10])

    def test_parse_proof(self):
        output_filename, zok_dir = compile_zokrates(example, output_dir, 'TUV')
        proof = generate_proof(zok_dir, [3, 9])
        self.assertIn('input', proof)
        self.assertIn('proof', proof)


example = """
def main(private field a, field b) -> (field):
	field result = if a * a == b then 1 else 0 fi
	result == 1
	return 1
"""

example_encryption = """
def dec(field msg, field key) -> (field):
	return msg - key

def enc(field msg, field R, field key) -> (field):
	return msg + key

def main(field gensubexpr1, field gensubexpr2, private field gensk1) -> (field):
	gensubexpr2 == dec(gensubexpr1, gensk1)
	return 1
"""
