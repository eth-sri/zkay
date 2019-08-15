from unittest import TestCase

from parameterized import parameterized_class

from bpl_ast.ast import SourceUnit, VariableDeclarationStatement, IdentifierExpr, \
	AssignmentStatement, Block
from bpl_ast.build_ast import build_ast
from bpl_ast.pointers.parent_setter import set_parents
from bpl_ast.pointers.symbol_table import fill_symbol_table, link_identifiers
from examples.examples import simple, simple_storage, all_examples
from examples.test_examples import TestExamples


class TestSimpleAST(TestCase):

	def get_ast_elements(self, ast: SourceUnit):
		self.contract = ast.contracts[0]
		self.f = self.contract.function_definitions[0]
		self.body = self.f.body
		self.decl_statement = self.body.statements[0]
		assert(isinstance(self.decl_statement, VariableDeclarationStatement))
		self.decl = self.decl_statement.variable_declaration
		self.assignment = self.body.statements[1]
		assert(isinstance(self.assignment, AssignmentStatement))
		self.identifier_expr = self.assignment.lhs
		assert(isinstance(self.identifier_expr, IdentifierExpr))

	def test_fill_symbol_table(self):
		ast = build_ast(simple.code())
		fill_symbol_table(ast)

		self.get_ast_elements(ast)

		self.assertDictEqual(ast.names, {'Simple': self.contract.idf})
		self.assertDictEqual(self.contract.names, {'f': self.f.idf})
		self.assertDictEqual(self.body.names, {'x': self.decl.idf})

	def test_link_identifiers(self):
		ast = build_ast(simple.code())
		set_parents(ast)
		link_identifiers(ast)

		self.get_ast_elements(ast)

		self.assertEqual(self.identifier_expr.target, self.decl)
		self.assertEqual(self.identifier_expr.get_annotated_type(), self.decl.annotated_type)


class TestSimpleStorageAST(TestCase):

	def test_fill_symbol_table(self):
		ast = build_ast(simple_storage.code())
		fill_symbol_table(ast)

		contract = ast.contracts[0]
		self.assertDictEqual(ast.names, {'SimpleStorage': contract.idf})

	def test_link_identifiers(self):
		ast = build_ast(simple_storage.code())
		set_parents(ast)
		link_identifiers(ast)
		assignment = ast['SimpleStorage']['set'].body[0]
		self.assertIsInstance(assignment, AssignmentStatement)

		stored_data = assignment.lhs.target
		self.assertEqual(stored_data, ast['SimpleStorage']['storedData'])

		x = assignment.rhs.target
		self.assertEqual(x.idf.name, 'x')


@parameterized_class(('name', 'example'), all_examples)
class TestSymbolTable(TestExamples):

	def test_symbol_table(self):
		ast = build_ast(self.example.code())
		set_parents(ast)
		fill_symbol_table(ast)
		link_identifiers(ast)
		contract = ast.contracts[0]
		self.assertEqual(contract.idf.name, self.name)
