from parameterized import parameterized_class

from examples.examples import all_examples
from examples.test_examples import TestExamples
from zkay_ast.ast import SourceUnit
from zkay_ast.build_ast import build_ast
from zkay_ast.pointers.parent_setter import set_parents
from zkay_ast.visitor.visitor import AstVisitor


class ParentChecker(AstVisitor):

    def visit(self, ast):
        if not isinstance(ast, SourceUnit):
            assert (ast.parent is not None)
        self._visit_internal(ast)


@parameterized_class(('name', 'example'), all_examples)
class TestParentSetter(TestExamples):

    def test_root_children_have_parent(self):
        ast = build_ast(self.example.code())
        set_parents(ast)

        # test
        for c in ast.children():
            self.assertEqual(c.parent, ast)

    def test_contract_identifier(self):
        ast = build_ast(self.example.code())
        set_parents(ast)

        # test
        contract = ast.contracts[0]
        idf = contract.idf
        self.assertEqual(idf.parent, contract)

    def test_all_nodes_have_parent(self):
        ast = build_ast(self.example.code())
        set_parents(ast)

        # test
        v = ParentChecker()
        v.visit(ast)
