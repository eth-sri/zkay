from parameterized import parameterized_class

from zkay.examples.examples import all_examples
from zkay.tests.utils.test_examples import TestExamples
from zkay.solidity_parser.emit import Emitter, normalize_code
from zkay.solidity_parser.parse import MyParser


@parameterized_class(('name', 'example'), all_examples)
class TestEmitEmpty(TestExamples):

    def setUp(self):
        self.p = MyParser(self.example.code())

    def test_emit(self):
        v = Emitter(self.p.tokens)
        result = v.visit(self.p.tree)
        self.assertEqual(self.example.code(), result)

    def test_normalize_code(self):
        normalized_reference = self.example.normalized()
        if normalized_reference:
            normalized = normalize_code(self.example.code())
            self.assertEqual(normalized, normalized_reference)
