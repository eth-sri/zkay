import os
from unittest import TestCase

from zkay.compiler.solidity.compiler import compile_solidity_code, compile_solidity_json
from zkay.examples.examples import others_dir

simple_storage = """
pragma solidity ^0.5.0;

contract SimpleStorage {
    uint storedData;

    function set(uint x) public {
        storedData = x;
    }

    function get() public view returns (uint) {
        return storedData;
    }
}"""

script_dir = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(script_dir, 'output')


class TestCompileSolidity(TestCase):

    def test_compile_solidity(self):
        compile_output = compile_solidity_code(simple_storage, output_dir)
        self.assertIsNotNone(compile_output)

    def test_compile_with_import(self):
        compile_output = compile_solidity_json(os.path.join(others_dir, 'AddUser.sol'), output_dir=output_dir)
        self.assertIsNotNone(compile_output)
