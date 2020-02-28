# Use regular expression replacements (stack program for reveal) to strip all zkay specific language features
# so that code can be passed to solc for type checking.

import re
from typing import Pattern
from zkay.config import cfg

# Declaration for me which is injected into each contract
ME_DECL = ' address private me = msg.sender;'

# ---------  Lexer Rules ---------

WS_PATTERN = r'[ \t\r\n\u000C]'
ID_PATTERN = r'[a-zA-Z\$_][a-zA-Z0-9\$_]*'
UINT_PATTERN = r'uint|uint8|uint16|uint24|uint32|uint40|uint48|uint56|uint64|uint72|uint80|uint88|uint96|uint104|uint112|uint120|uint128|uint136|uint144|uint152|uint160|uint168|uint176|uint184|uint192|uint200|uint208|uint216|uint224|uint232|uint240|uint248|uint256'
INT_PATTERN = r'int|int8|int16|int24|int32|int40|int48|int56|int64|int72|int80|int88|int96|int104|int112|int120|int128|int136|int144|int152|int160|int168|int176|int184|int192|int200|int208|int216|int224|int232|int240|int248|int256'
USER_TYPE_PATTERN = f'(?:(?:{ID_PATTERN}\\.)*(?:{ID_PATTERN}))'
ELEM_TYPE_PATTERN = r'(?:address|address payable|bool|' + UINT_PATTERN + '|' + INT_PATTERN + '|' + USER_TYPE_PATTERN + ')'
NONID_START = r'(?:[^a-zA-Z0-9\$_]|^)'
NONID_END = r'(?:[^a-zA-Z0-9\$_]|$)'
PARENS_PATTERN = re.compile(r'[()]')
BRACE_PATTERN = re.compile(r'[{}]')
STRING_OR_COMMENT_PATTERN = re.compile(
    r'(?P<repl>'
    r'(?://[^\r\n]*)'                           # match line comment
    r'|(?:/\*.*?\*/)'                           # match block comment
    r"|(?:(?<=')(?:[^'\r\n\\]|(?:\\.))*(?='))"  # match single quoted string literal
    r'|(?:(?<=")(?:[^"\r\n\\]|(?:\\.))*(?="))'  # match double quoted string literal
    r')', re.DOTALL
)

# ---------  Parsing ---------
CONTRACT_START_PATTERN = re.compile(f'{NONID_START}contract{WS_PATTERN}*{ID_PATTERN}{WS_PATTERN}*(?=[{{])')

# Regex to match annotated types
ATYPE_PATTERN = re.compile(f'(?P<keep>{NONID_START}{ELEM_TYPE_PATTERN}{WS_PATTERN}*)'  # match basic type
                           f'(?P<repl>@{WS_PATTERN}*{ID_PATTERN})')             # match @owner

# Regexes to match 'all' and 'final'
MATCH_WORD_FSTR = f'(?P<keep>{NONID_START})(?P<repl>{{}})(?={NONID_END})'
FINAL_PATTERN = re.compile(MATCH_WORD_FSTR.format('final'))
ALL_PATTERN = re.compile(MATCH_WORD_FSTR.format('all'))

# Pragma regex
PRAGMA_PATTERN = re.compile(f'(?P<keep>{NONID_START}pragma\\s*)(?P<repl>zkay.*?);')

# Regex to match tagged mapping declarations
MAP_PATTERN = re.compile(
    f'(?P<keep>{NONID_START}mapping{WS_PATTERN}*\\({WS_PATTERN}*{ELEM_TYPE_PATTERN}{WS_PATTERN}*)'  # match 'mapping (address'
    f'(?P<repl>!{WS_PATTERN}*{ID_PATTERN})'                                             # match '!tag'
    f'(?={WS_PATTERN}*=>{WS_PATTERN}*)')                                                # expect '=>'

# Regex to detect start of reveal
REVEAL_START_PATTERN = re.compile(f'(?:^|(?<=[^\\w]))reveal{WS_PATTERN}*(?=\\()')  # match 'reveal', expect '('


def create_surrogate_string(instr: str):
    """
    Preserve newlines and replace all other characters with spaces

    :return whitespace string with same length as instr and with the same line breaks
    """
    return ''.join(['\n' if e == '\n' else ' ' for e in instr])


def find_matching_parenthesis(code: str, open_parens_loc: int) -> int:
    """
    Get index of matching parenthesis/bracket/brace.

    :param code: code in which to search
    :param open_parens_loc: index of the opening parenthesis within code
    :return: index of the matching closing parenthesis
    """

    # Determine parenthesis characters
    open_sym = code[open_parens_loc]
    if open_sym == '(':
        close_sym = ')'
    elif open_sym == '{':
        close_sym = '}'
    elif open_sym == '[':
        close_sym = ']'
    else:
        raise ValueError('Unsupported parenthesis type')

    pattern = re.compile(f'[{open_sym}{close_sym}]')
    idx = open_parens_loc + 1
    open = 1
    while open > 0:
        cstr = code[idx:]
        idx += re.search(pattern, cstr).start()
        open += 1 if code[idx] == open_sym else -1
        idx += 1
    return idx - 1


# Replacing reveals only with regex is impossible because they could be nested -> do it with a stack
def strip_reveals(code: str):
    """Replace reveal expressions by their inner expression, with whitespace padding."""
    matches = re.finditer(REVEAL_START_PATTERN, code)
    for m in matches:
        before_reveal_loc = m.start()
        reveal_open_parens_loc = m.end()

        # Find matching closing parenthesis
        reveal_close_parens_loc = find_matching_parenthesis(code, reveal_open_parens_loc)

        # Go backwards to find comma before owner tag
        last_comma_loc = code[:reveal_close_parens_loc].rfind(',')

        # Replace reveal by its inner expression + padding
        code = f'{code[:before_reveal_loc]}' \
               f'{create_surrogate_string(code[before_reveal_loc:reveal_open_parens_loc])}' \
               f'{code[reveal_open_parens_loc:last_comma_loc]}' \
               f'{create_surrogate_string(code[last_comma_loc:reveal_close_parens_loc])}' \
               f'{code[reveal_close_parens_loc:]}'
    return code


def inject_me_decls(code: str):
    """Add an additional address me = msg.sender state variable declaration right before the closing brace of each contract definition."""
    matches = re.finditer(CONTRACT_START_PATTERN, code)
    insert_indices = []
    for m in matches:
        insert_indices.append(find_matching_parenthesis(code, m.end()))
    parts = [code[i:j] for i, j in zip([0] + insert_indices, insert_indices + [None])]
    return ME_DECL.join(parts)


def replace_with_surrogate(code: str, search_pattern: Pattern, replacement_fstr: str = '{}'):
    """
    Replace all occurrences of search_pattern with capture group <keep> (if any) + replacement.

    Replacement is either
        a) replacement_fstr (if replacement_fstr does not contain '{}')
        b) replacement_fstr with {} replaced by whitespace corresponding to content of capture group <repl>
           (such that replacement length == <repl> length with line breaks preserved)

    The <repl> capture group must be the last thing that is matched in search pattern
    """
    keep_repl_pattern = r'\g<keep>' if '(?P<keep>' in search_pattern.pattern else ''
    has_ph = '{}' in replacement_fstr
    replace_len = len(replacement_fstr) - 2
    replacement = replacement_fstr
    search_idx = 0
    while True:
        match = re.search(search_pattern, code[search_idx:])
        if match is None:
            return code
        if has_ph:
            replacement = replacement_fstr.format(create_surrogate_string(match.groupdict()["repl"])[replace_len:])

        code = code[:search_idx] + re.sub(search_pattern, keep_repl_pattern + replacement, code[search_idx:], count=1)
        search_idx += match.end() + 1


def fake_solidity_code(code: str):
    """
    Returns the solidity code to which the given zkay_code corresponds when dropping all privacy features,
    while preserving original formatting
    """

    # Strip string literals and comments
    code = replace_with_surrogate(code, STRING_OR_COMMENT_PATTERN)

    # Replace zkay pragma with solidity pragma
    code = replace_with_surrogate(code, PRAGMA_PATTERN, f'solidity {cfg.zkay_solc_version_compatibility};')

    # Strip final
    code = replace_with_surrogate(code, FINAL_PATTERN)

    # Strip ownership annotations
    code = replace_with_surrogate(code, ATYPE_PATTERN)

    # Strip map key tags
    code = replace_with_surrogate(code, MAP_PATTERN)

    # Strip reveal expressions
    code = strip_reveals(code)

    # Inject me address declaration (should be okay for type checking, maybe not for program analysis)
    # An alternative would be to replace me by msg.sender, but this would affect code length (error locations)
    code = inject_me_decls(code)

    return code
