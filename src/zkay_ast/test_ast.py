from unittest import TestCase

from zkay_ast.ast import BooleanLiteralExpr, RequireStatement, Identifier, IdentifierExpr, AssignmentStatement, \
    BuiltinFunction, FunctionCallExpr, NumberLiteralExpr


class TestASTSimpleStorageDetailed(TestCase):

    def test_require(self):
        e = BooleanLiteralExpr(True)
        r = RequireStatement(e)
        self.assertEqual(str(r), 'require(true);')

    def test_assignment_statement(self):
        i = Identifier('x')
        lhs = IdentifierExpr(i)
        rhs = BooleanLiteralExpr(True)
        a = AssignmentStatement(lhs, rhs)
        self.assertIsNotNone(a)
        self.assertEqual(str(a), 'x = true;')
        self.assertEqual(a.children(), [lhs, rhs])
        self.assertDictEqual(a.names, {})
        self.assertIsNone(a.parent)

    def test_builtin_arity(self):
        f = BuiltinFunction('+')
        self.assertEqual(f.arity(), 2)

    def test_builtin_code(self):
        f = BuiltinFunction('+')
        c = FunctionCallExpr(f, [NumberLiteralExpr(0), NumberLiteralExpr(0)])
        self.assertEqual(c.code(), '0 + 0')
