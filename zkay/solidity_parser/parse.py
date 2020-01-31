from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from zkay.solidity_parser.generated.SolidityLexer import SolidityLexer
from zkay.solidity_parser.generated.SolidityParser import SolidityParser


class SyntaxException(Exception):
    """
    Error during parsing"
    """

    def __init__(self, msg: str, ctx=None, code=None) -> None:
        if ctx is not None:
            assert code is not None
            from zkay.zkay_ast.ast import get_code_error_msg
            msg = f'{get_code_error_msg(ctx.start.line, ctx.start.column + 1, str(code).splitlines())}\n{msg}'
        super().__init__(msg)


class MyErrorListener(ErrorListener):

    def __init__(self, code):
        super(MyErrorListener, self).__init__()
        self.code = code

    def syntaxError(self, recognizer, offending_symbol, line, column, msg, e):
        from zkay.zkay_ast.ast import get_code_error_msg
        report = f'{get_code_error_msg(line, column + 1, str(self.code).splitlines())}\n{msg}'
        raise SyntaxException(report)


class MyParser:

    def __init__(self, code):
        if isinstance(code, str):
            self.stream = InputStream(code)
        else:
            self.stream = code
        self.lexer = SolidityLexer(self.stream)
        self.lexer._listeners = [MyErrorListener(code)]
        self.tokens = CommonTokenStream(self.lexer)
        self.parser = SolidityParser(self.tokens)
        self.parser._listeners = [MyErrorListener(code)]
        self.tree = self.parser.sourceUnit()


def get_parse_tree(code):
    p = MyParser(code)
    return p.tree
