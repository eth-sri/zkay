from textwrap import indent, dedent
from typing import Union, Iterable


class MultiLineFormatter:
    def __init__(self, block_start_char=' {', block_end_char='}') -> None:
        self.text = ''
        self.current_indent = ''
        self.block_start_char = block_start_char
        self.block_end_char = block_end_char

    def __mul__(self, other: Union[str, Iterable[str]]) -> 'MultiLineFormatter':
        if isinstance(other, str):
            return self.append(other)
        else:
            for elem in other:
                self.append(elem)
            return self

    def __truediv__(self, other: str) -> 'MultiLineFormatter':
        return self.indent() * other

    def __floordiv__(self, other) -> 'MultiLineFormatter':
        return self.dedent() * other

    def append(self, txt: str) -> 'MultiLineFormatter':
        self.text += indent(dedent(txt) + '\n', self.current_indent)
        return self

    def indent(self) -> 'MultiLineFormatter':
        self.current_indent += ' ' * 4
        return self

    def dedent(self) -> 'MultiLineFormatter':
        self.current_indent = self.current_indent[:-4]
        return self
