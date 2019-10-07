
# Use regular expression replacements (stack program for reveal) to strip all zkay specific language features
# so that code can be passed to solc for type checking

import re
from typing import Optional

ME_DECL = ' address private me = msg.sender;'

# Whitespace
WSPATTERN = r'[ \t\r\n\u000C]'

# Identifier
IDPATTERN = r'[a-zA-Z\$_][a-zA-Z0-9\$_]*'

# Type
BTPATTERN = r'(?:address|bool|uint)'

# Match what is adjacent to word (type, identifier, keyword)
NONIDSTART = r'(?:[^\w]|^)'
NONIDEND = r'(?:[^\w]|$)'

# Match comments
COMMENT_PATTERN = re.compile(r'(?P<repl>(?://[^\r\n]*)|(?:/\*.*?\*/))', re.DOTALL)

# Regex to match contract declaration
CONTRACT_DECL_PATTERN = re.compile(f'(?P<keep>{NONIDSTART}contract{WSPATTERN}*{IDPATTERN}{WSPATTERN}*{"{"}[^\\n]*?)'
								   f'(?<!{ME_DECL})(?P<repl>\\n)')

# Regex to match annotated types
ATYPE_PATTERN = re.compile(f'(?P<keep>{NONIDSTART}{BTPATTERN}{WSPATTERN}*)' # match basic type
						   f'(?P<repl>@{WSPATTERN}*{IDPATTERN})')           # match @owner

# Regex to match 'final' keyword
FINAL_PATTERN = re.compile(f'(?P<keep>{NONIDSTART})' # match before final
						   f'(?P<repl>final)'        # match final
						   f'(?={NONIDEND})')        # match after final

# Regex to match 'all' keyword
ALL_PATTERN = re.compile(f'(?P<keep>{NONIDSTART})' # match before all
						 f'(?P<repl>all)'          # match all
						 f'(?={NONIDEND})')        # match after all

# Regex to match tagged mapping declarations
MAP_PATTERN = re.compile(f'(?P<keep>{NONIDSTART}mapping{WSPATTERN}*\\({WSPATTERN}*address{WSPATTERN}*)' # match 'mapping (address'
						 f'(?P<repl>!{WSPATTERN}*{IDPATTERN})'                                          # match '!tag'
						 f'(?={WSPATTERN}*=>{WSPATTERN}*)')                                             # match '=>'

# Regex to detect start of reveal
REVEAL_START_PATTERN = re.compile(f'(?:^|(?<=[^\\w]))reveal{WSPATTERN}*\\(') # match 'reveal('

PARENS_PATTERN = re.compile(r'[()]')


# Replacing reveals only with regex is impossible because they could be nested -> do it with a stack
def strip_reveals(code: str):
	while True:
		# Get position of next reveal expression
		m = re.search(REVEAL_START_PATTERN, code)
		if not m:
			return code

		before_reveal_loc = m.start()
		inside_reveal_loc = m.end()

		# Find matching closing parenthesis
		idx = inside_reveal_loc
		open = 1
		while open > 0:
			cstr = code[idx:]
			idx += re.search(PARENS_PATTERN, cstr).start()
			open += 1 if code[idx] == '(' else -1
			idx += 1

		# Go backwards to find comma before owner tag
		last_comma_loc = code[:idx].rfind(',')
		after_reveal_loc = idx

		# Preserve parenthesis
		inside_reveal_loc -= 1
		after_reveal_loc -= 1

		# Replace reveal by its inner expression + padding
		code = f'{code[:before_reveal_loc]}' \
			   f'{create_surrogate_string(code[before_reveal_loc:inside_reveal_loc])}' \
			   f'{code[inside_reveal_loc:last_comma_loc]}' \
			   f'{create_surrogate_string(code[last_comma_loc:after_reveal_loc])}' \
			   f'{code[after_reveal_loc:]}'


def create_surrogate_string(instr: str):
	"""
	Preserve newlines and replace all other characters with spaces
	:return whitespace string with same length as instr and with the same line breaks
	"""
	return ''.join(['\n' if e == '\n' else ' ' for e in instr])


def replace_with_surrogate(code: str, search_pattern: re.Pattern, surrogate_text: Optional[str]= None):
	keep_repl_pattern = r'\g<keep>' if '(?P<keep>' in search_pattern.pattern else ''
	while True:
		match = re.search(search_pattern, code)
		if match is None:
			return code

		rep_pattern = keep_repl_pattern + \
					  (create_surrogate_string(match.groupdict()["repl"]) if surrogate_text is None else surrogate_text)

		code = re.sub(search_pattern, rep_pattern, code, count=1)


def fake_solidity_code(zkay_code: str):
	"""
	Returns the solidity code to which the given zkay_code corresponds when dropping all privacy features,
	while preserving original formatting
	"""

	code = zkay_code

	# Strip comments
	code = replace_with_surrogate(code, COMMENT_PATTERN)

	# Strip final
	code = replace_with_surrogate(code, FINAL_PATTERN)

	# Strip ownership annotations
	code = replace_with_surrogate(code, ATYPE_PATTERN)

	# Strip map key tags
	code = replace_with_surrogate(code, MAP_PATTERN)

	# Strip reveal expressions
	code = strip_reveals(code)

	# 'all' should have been removed by first step
	assert re.search(ALL_PATTERN, code) is None

	# Inject me address declaration (should be okay for type checking, maybe not for program analysis)
	# An alternative would be to replace me by msg.sender, but this would affect code length (error locations)
	code = replace_with_surrogate(code, CONTRACT_DECL_PATTERN, ME_DECL + '\n')

	return code
