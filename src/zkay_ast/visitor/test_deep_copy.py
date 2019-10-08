from parameterized import parameterized_class

from examples.examples import all_examples
from examples.test_examples import TestExamples
from zkay_ast.build_ast import build_ast
from zkay_ast.visitor.deep_copy import deep_copy


@parameterized_class(('name', 'example'), all_examples)
class TestParentSetter(TestExamples):

    def test_deep_copy(self):
        ast = build_ast(self.example.code())
        ast_2 = deep_copy(ast)
        self.assertEqual(str(ast), str(ast_2))
