import re
from unittest import TestCase

from parameterized import parameterized_class

from examples.examples import analysis, all_examples
from examples.test_examples import TestExamples
from zkay_ast.analysis.alias_analysis import alias_analysis
from zkay_ast.ast import Statement, CodeVisitor, AST
from zkay_ast.build_ast import build_ast
from zkay_ast.pointers.parent_setter import set_parents
from zkay_ast.pointers.symbol_table import link_identifiers


class TestAliasAnalysisDetail(TestCase):

    def test_alias_analysis(self):
        # perform analysis
        ast = build_ast(analysis.code())
        set_parents(ast)
        link_identifiers(ast)
        alias_analysis(ast)

        # generate string, including analysis results
        v = AnalysisCodeVisitor()
        s = v.visit(ast)
        s = re.sub(" +\n", "\n", s)
        # next statement can be enabled to determine the computed output
        # print(s)

        # check output
        self.maxDiff = None
        self.assertMultiLineEqual(analysis.code(), s)


@parameterized_class(('name', 'example'), all_examples)
class TestAliasAnalysis(TestExamples):

    def test_alias_analysis(self):
        # perform analysis
        ast = build_ast(self.example.code())
        set_parents(ast)
        link_identifiers(ast)
        alias_analysis(ast)


class AnalysisCodeVisitor(CodeVisitor):

    def visit(self, ast: AST):
        s = super().visit(ast)
        if isinstance(ast, Statement):
            b = str(ast.before_analysis)
            a = str(ast.after_analysis)
            s = f'\n// {b}\n{s}\n// {a}\n'
        return s
