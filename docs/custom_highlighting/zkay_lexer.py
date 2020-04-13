# -*- coding: utf-8 -*-
"""
    Based on the Lexer for the Solidity language.

    :copyright: (Solidity Lexer) Copyright 2006-2015 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from pygments.lexer import RegexLexer, include, bygroups, default, using, \
    this, words, combined
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation, Other

__all__ = ['ZkayLexer']


class ZkayLexer(RegexLexer):
    """
    For Solidity source code.
    """

    name = 'zkay'
    aliases = ['zkay']
    filenames = ['*.sol', '*.zkay']
    mimetypes = []

    flags = re.DOTALL | re.UNICODE | re.MULTILINE

    def type_names(prefix, sizerange):
        """
        Helper for type name generation, like: bytes1 .. bytes32
        """
        namelist = []
        for i in sizerange: namelist.append(prefix + str(i))
        return tuple(namelist)

    def type_names_mn(prefix, sizerangem, sizerangen):
        """
        Helper for type name generation, like: fixed0x8 .. fixed0x256
        """
        lm = []
        ln = []
        namelist = []

        # construct lists out of ranges
        for i in sizerangem: lm.append(i)
        for i in sizerangen: ln.append(i)

        # sizes (in bits) are valid if (%8 == 0) and (m+n <= 256)
        # first condition is covered by passing proper sizerange{m,n}
        validpairs = [tuple([m,n]) for m in lm for n in ln if m+n<=256]
        for i in validpairs:
            namelist.append(prefix + str(i[0]) + 'x' + str(i[1]))

        return tuple(namelist)


    tokens = {
        'assembly': [
            include('comments'),
            include('numbers'),
            include('strings'),
            include('whitespace'),

            (r'\{', Punctuation, '#push'),
            (r'\}', Punctuation, '#pop'),
            (r'[(),]', Punctuation),
            (r':=|=:', Operator),
            (r'(let)(\s*)(\w*\b)', bygroups(Operator.Word, Text, Name.Variable)),
            (r'(\w*\b)(\:[^=])', bygroups(Name.Label, Punctuation)),

            (r'if\b', Keyword.Reserved),

            # evm instructions
            (r'(stop|add|mul|sub|div|sdiv|mod|smod|addmod|mulmod|exp|'
             r'signextend|lt|gt|slt|sgt|eq|iszero|and|or|xor|not|byte|'
             r'keccak256|sha3|address|balance|origin|caller|'
             r'callvalue|calldataload|calldatasize|calldatacopy|'
             r'codesize|codecopy|gasprice|extcodesize|extcodecopy|'
             r'blockhash|coinbase|timestamp|number|difficulty|gaslimit|'
             r'pop|mload|mstore|mstore8|sload|sstore|for|switch|'
             r'jump|jumpi|pc|msize|gas|jumpdest|push1|push2|'
             r'push32|dup1|dup2|dup16|swap1|swap2|swap16|log0|log1|log4|'
             r'create|call|callcode|return|delegatecall|suicide|'
             r'returndatasize|returndatacopy|staticcall|revert|invalid)\b',
             Name.Function),

            # everything else is either a local/external var, or label
            ('[a-zA-Z_]\w*', Name)
        ],
        # TODO: Yul parsing (not implemented ATM)
        #'yul': [],
        'natspec': [
            (r'@(author|dev|notice|param|return|title)\b', Comment.Special),
        ],
        'comment-parse-single': [
            include('natspec'),
            (r'\n', Comment.Single, '#pop'),
            (r'[^\n]', Comment.Single),
        ],
        'comment-parse-multi': [
            include('natspec'),
            (r'[^*/]', Comment.Multiline),
            (r'\*/', Comment.Multiline, '#pop'),
            (r'[*/]', Comment.Multiline),
        ],
        'comments': [
            (r'//', Comment.Single, 'comment-parse-single'),
            (r'/[*]', Comment.Multiline, 'comment-parse-multi'),
        ],
        'keywords-other': [
            (words(('for', 'in', 'while', 'do', 'break', 'return',
                    'returns', 'continue', 'if', 'else', 'throw',
                    'new', 'delete', 'try', 'catch'),
                   suffix=r'\b'), Keyword),

            (r'assembly\b', Keyword, 'assembly'),

            (words(('contract', 'interface', 'enum', 'event', 'function',
                    'constructor', 'library', 'mapping', 'modifier',
                    'struct', 'var'),
                   suffix=r'\b'), Keyword.Declaration),

            (r'(import|using)\b', Keyword.Namespace),

            # pragmas are not pragmatic in their formatting :/
            (r'pragma( experimental| solidity|)\b', Keyword.Reserved),
            # misc keywords
            (r'(_|as|constant|default|from|is)\b', Keyword.Reserved),
            (r'emit\b', Keyword.Reserved),
            # built-in modifier
            (r'payable\b', Keyword.Reserved),
            (r'final\b', Keyword.Reserved),
            # variable location specifiers
            (r'(memory|storage)\b', Keyword.Reserved),
            # method visibility specifiers
            (r'(external|internal|private|public)\b', Keyword.Reserved),
            # event parameter specifiers
            (r'(anonymous|indexed)\b', Keyword.Reserved),
            # added in solc v0.4.0, not covered elsewhere
            (r'(abstract|pure|static|view)\b', Keyword.Reserved),
            # access to contracts' codes and name
            (r'type\(.*\)\.(creationCode|runtimeCode|name)\b', Keyword.Reserved),

            # reserved for future use since solc v0.5.0
            (words(('alias', 'apply', 'auto', 'copyof', 'define', 'immutable',
                    'implements', 'macro', 'mutable', 'override', 'partial',
                    'promise', 'reference', 'sealed', 'sizeof', 'supports',
                    'typedef', 'unchecked'),
                   suffix=r'\b'), Keyword.Reserved),
            # reserved for future use since solc v0.6.0
            (r'virtual\b', Keyword.Reserved),

            # built-in constants
            (r'(true|false)\b', Keyword.Constant),
            (r'(wei|finney|szabo|ether)\b', Keyword.Constant),
            (r'(seconds|minutes|hours|days|weeks|years)\b', Keyword.Constant),
        ],
        'keywords-types': [
            (words(('address', 'bool', 'byte', 'bytes', 'int', 'fixed',
                    'string', 'ufixed', 'uint', 'type'),
                   suffix=r'\b|@'), Keyword.Type),

            (words(type_names('int', range(8, 256+1, 8)),
                   suffix=r'\b|@'), Keyword.Type),
            (words(type_names('uint', range(8, 256+1, 8)),
                   suffix=r'\b|@'), Keyword.Type),
            (words(type_names('bytes', range(1, 32+1)),
                   suffix=r'\b|@'), Keyword.Type),
            (words(type_names_mn('fixed', range(8, 256+1, 8), range(0, 80+1, 1)),
                   suffix=r'\b'), Keyword.Type),
            (words(type_names_mn('ufixed', range(8, 256+1, 8), range(0, 80+1, 1)),
                   suffix=r'\b'), Keyword.Type),
        ],
        'keywords-nested': [
            (r'abi\.encode(|Packed|WithSelector|WithSignature)\b', Name.Builtin),
            (r'block\.(blockhash|coinbase|difficulty|gaslimit|hash|number|timestamp)\b', Name.Builtin),
            (r'msg\.(data|gas|sender|value)\b', Name.Builtin),
            (r'tx\.(gasprice|origin)\b', Name.Builtin),
        ],
        'numbers': [
            (r'0[xX][0-9a-fA-F]+', Number.Hex),
            (r'[0-9][0-9]*\.[0-9]+([eE][0-9]+)?', Number.Float),
            (r'[0-9]+([eE][0-9]+)?', Number.Integer),
        ],
        'string-parse-common': [
            # escapes
            (r'\\(u[0-9a-fA-F]{4}|x..|[^x])', String.Escape),
            # almost everything else is plain characters
            (r'[^\\"\'\n]+', String),
            # line continuation
            (r'\\\n', String),
            # stray backslash
            (r'\\', String)
        ],
        'string-parse-double': [
            (r'"', String, '#pop'),
            (r"'", String)
        ],
        'string-parse-single': [
            (r"'", String, '#pop'),
            (r'"', String)
        ],
        'strings': [
            # hexadecimal string literals
            (r"hex'[0-9a-fA-F]+'", String),
            (r'hex"[0-9a-fA-F]+"', String),
            # usual strings
            (r'"', String, combined('string-parse-common',
                                    'string-parse-double')),
            (r"'", String, combined('string-parse-common',
                                    'string-parse-single'))
        ],
        'whitespace': [
            (r'\s+', Text)
        ],
        'root': [
            include('comments'),
            include('keywords-types'),
            include('keywords-nested'),
            include('keywords-other'),
            include('numbers'),
            include('strings'),
            include('whitespace'),

            (r'\+\+|--|\*\*|\?|:|~|&&|\|\||=>|==?|!=?|'
             r'(<<|>>>?|[-<>+*%&|^/])=?', Operator),

            (r'[{(\[;,]', Punctuation),
            (r'[})\].]', Punctuation),

            # compiler built-ins
            (r'(this|super|me|all|owner|alice|bob)\b', Name.Builtin),
            (r'selector\b', Name.Builtin),

            # receive/fallback functions
            (r'(receive|fallback)\b', Keyword.Function),

            # like block.hash and msg.gas in `keywords-nested`
            (r'(blockhash|gasleft)\b', Name.Function),

            # actually evm instructions, should be Name.Function?..
            (r'(balance|now)\b', Name.Builtin),
            (r'(selfdestruct|suicide)\b', Name.Builtin),

            # processed into many-instructions
            (r'(send|transfer|call|callcode|delegatecall)\b', Name.Function),
            (r'(assert|revert|require)\b', Name.Function),
            (r'push\b', Name.Function),

            # built-in functions and/or precompiles
            (r'(addmod|ecrecover|keccak256|mulmod|ripemd160|sha256|sha3|reveal)\b',
             Name.Function),

            # everything else is a var/function name
            ('[a-zA-Z_]\w*', Name)
        ] # 'root'
    } # tokens
