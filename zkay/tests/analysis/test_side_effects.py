from parameterized import parameterized_class

from zkay.examples.examples import all_examples
from zkay.tests.utils.test_examples import TestExamples
from zkay.zkay_ast.analysis.side_effects import detect_expressions_with_side_effects
from zkay.zkay_ast.build_ast import build_ast
from zkay.zkay_ast.process_ast import process_ast, get_processed_ast


@parameterized_class(('name', 'example'), all_examples)
class TestSideEffects(TestExamples):

    def has_side_effects(self):
        if self.name in ['Addition', 'Simple']:
            return True
        elif self.name in ['MappingNameConflict', 'Empty']:
            return False
        else:
            return None

    def test_side_effects(self):
        ast = get_processed_ast(self.example.code(), type_check=False, solc_check=False)
        e = detect_expressions_with_side_effects(ast)
        if self.has_side_effects() is not None:
            self.assertEqual(e, self.has_side_effects())
