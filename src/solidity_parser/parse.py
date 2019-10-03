from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from solidity_parser.generated.SolidityLexer import SolidityLexer
from solidity_parser.generated.SolidityParser import SolidityParser


class SyntaxException(Exception):
	"""
	Error during parsing"
	"""
	pass


class MyErrorListener(ErrorListener):

	def __init__(self, code):
		super(MyErrorListener, self).__init__()
		self.code = code

	def syntaxError(self, recognizer, offending_symbol, line, column, msg, e):
		from zkay_ast.ast import get_code_error_msg
		report = f'{get_code_error_msg(line, column + 1, str(self.code).splitlines())}\n{msg}'
		raise SyntaxException(report)


class MyParser:

	def __init__(self, code):
		if isinstance(code, str):
			self.stream = InputStream(code)
		else:
			self.stream = code
		self.lexer = SolidityLexer(self.stream)
		self.tokens = CommonTokenStream(self.lexer)
		self.parser = SolidityParser(self.tokens)
		self.parser._listeners = [MyErrorListener(code)]
		self.tree = self.parser.sourceUnit()


def get_parse_tree(code):
	p = MyParser(code)
	return p.tree
