from antlr4 import CommonTokenStream, Token
from antlr4.Token import CommonToken

from solidity_parser.generated.SolidityVisitor import SolidityVisitor
from solidity_parser.parse import get_parse_tree


class Emitter(SolidityVisitor):

    def __init__(self, token_stream: CommonTokenStream = None):
        self.token_stream = token_stream
        self.next_token_index = 0
        self.emitted = ''

    def get_hidden_up_to(self, node):
        # handle unavailable token stream by using spaces
        if self.token_stream is None:
            if self.next_token_index == 0:
                self.next_token_index += 1
                return ''
            else:
                return ' '

        # when token stream available: add hidden tokens
        ret = ''

        token_index = node.getSourceInterval()[0]

        while self.next_token_index <= token_index:
            before: CommonToken = self.token_stream.get(self.next_token_index)
            if before.channel == CommonToken.HIDDEN_CHANNEL:
                ret += before.text
            self.next_token_index += 1

        return ret

    def visitTerminal(self, node):
        hidden = self.get_hidden_up_to(node)
        if node.getSymbol().type == Token.EOF:
            code = ''
        else:
            code = node.getText()

        self.emitted += hidden + code
        return self.emitted

    def visitChildren(self, node):
        for c in node.getChildren():
            c.accept(self)

        return self.emitted


def normalize_code(code):
    tree = get_parse_tree(code)
    emitter = Emitter()
    return emitter.visit(tree)
