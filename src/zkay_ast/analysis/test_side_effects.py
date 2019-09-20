from parameterized import parameterized_class

from zkay_ast.analysis.side_effects import has_side_effects
from examples.examples import all_examples
from zkay_ast.build_ast import build_ast
from examples.test_examples import TestExamples


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
		ast = build_ast(self.example.code())
		e = has_side_effects(ast)
		if self.has_side_effects() is not None:
			self.assertEqual(e, self.has_side_effects())
