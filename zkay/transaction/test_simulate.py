from unittest import TestCase

from zkay.examples.examples import addition, simple_storage
from zkay.transaction.simulate import Simulator
from zkay.zkay_ast.process_ast import get_processed_ast


class TestSimulator(TestCase):

    def test_addition(self):
        ast = get_processed_ast(addition.code())
        s = Simulator()

        s.call(ast['Addition']['f'], 'me', [1, 2])
        x = s.state_by_name()['x']
        self.assertEqual(x, 3)

    def test_simple_storage(self):
        ast = get_processed_ast(simple_storage.code())
        s = Simulator()

        s.call(ast['SimpleStorage']['constructor'], 'me', [])
        s.call(ast['SimpleStorage']['set'], 'me', [12])
        v = s.call(ast['SimpleStorage']['get'], 'me', [])
        self.assertEqual(v, 12)
