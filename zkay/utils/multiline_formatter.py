from textwrap import dedent, indent
from typing import Union, List


class MultiLineFormatter:
    """
    \\* operator -> add de-dented text (+ \\\\n), if operand is a list -> add \\\\n-joined elements

    % operator -> add de-dented text (+ \\\\n), if operand is a list -> add ,-joined elements

    / operator -> increase indentation level and add text (+ \\\\n)

    // operator -> decrease indentation level and add text (+ \\\\n)
    """
    def __init__(self, indent_str=' ' * 4) -> None:
        self.text = ''
        self.current_indent = ''
        self.indent_str = indent_str

    def __mul__(self, other: Union[str, List[str]]) -> 'MultiLineFormatter':
        if isinstance(other, str):
            return self.append(other)
        else:
            self.text += '\n'
            return self.append_lines(other)

    def __mod__(self, other: Union[str, List[str]]) -> 'MultiLineFormatter':
        if isinstance(other, str):
            return self.append(other, sep=', ')
        else:
            return self.append_lines(other, sep=', ')

    def __truediv__(self, other: str) -> 'MultiLineFormatter':
        if other:
            return self.indent() * other
        else:
            return self.indent()

    def __floordiv__(self, other) -> 'MultiLineFormatter':
        return self.dedent() * other

    def __str__(self) -> str:
        return f'{self.text.strip()}\n'

    def append(self, txt: str, sep='\n') -> 'MultiLineFormatter':
        self.text += sep
        if txt:
            self.text += indent(dedent(txt), self.current_indent)
        return self

    def append_lines(self, lines, sep='\n') -> 'MultiLineFormatter':
        self.text += sep.join(indent(dedent(t if t != '\n' else ''), self.current_indent) for t in lines if t)
        return self

    def indent(self) -> 'MultiLineFormatter':
        self.current_indent += self.indent_str
        return self

    def dedent(self) -> 'MultiLineFormatter':
        assert len(self.current_indent) >= len(self.indent_str)
        self.current_indent = self.current_indent[:-len(self.indent_str)]
        return self
