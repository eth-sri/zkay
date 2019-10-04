
# Use regular expression replacements to strip all zkay specific language features
# (so that code can be passed to solc for type checking)
# TODO? currently text inside comments is also processed

import re
from typing import Optional

ME_DECL = ' address private me = msg.sender;'

# Whitespace
WSPATTERN = r'[ \t\r\n\u000C]'

# Identifier
IDPATTERN = r'[a-zA-Z\$_][a-zA-Z\$_]*'

# Type
TPATTERN = r'(?:address|bool|uint)'

# Match what is adjacent to word (type, identifier, keyword)
NONIDSTART = r'(?:[^\w]|^)'
NONIDEND = r'(?:[^\w]|$)'

# Regex to match contract declaration
CONTRACTDEFPATTERN = re.compile(f'(?P<keep1>{NONIDSTART}contract{WSPATTERN}*{IDPATTERN}{WSPATTERN}*{"{"}[^\\n]*?)'
								f'(?<!{ME_DECL})(?P<repl>\\n)')

# Regex to match annotated types
ATYPEPATTERN = re.compile(f'(?P<keep1>{NONIDSTART}{TPATTERN}{WSPATTERN}*)' # match type
						  f'(?P<repl>@{WSPATTERN}*{IDPATTERN})'            # match @owner
						  f'(?P<keep2>{NONIDEND})')                        # match after owner

# Regex to match 'final' keyword
FINAL_PATTERN = re.compile(f'(?P<keep1>{NONIDSTART})' # match before all
						f'(?P<repl>final)'            # match 'final'
						f'(?P<keep2>{NONIDEND})')     # match after all

# Regex to match 'all' keyword
ALLPATTERN = re.compile(f'(?P<keep1>{NONIDSTART})' # match before all
						f'(?P<repl>all)'           # match 'all'
						f'(?P<keep2>{NONIDEND})')  # match after all

# Regex to match reveal expressions
REVEALPATTERN = re.compile(f'(?P<keep1>{NONIDSTART})(?P<repl1>reveal{WSPATTERN}*\\({WSPATTERN}*)' # match 'reveal('
						   f'(?P<expr>[^°]*?)'                                                    # lazily match any expression (currently assumes ° never occurs)
						   f'(?P<repl2>{WSPATTERN}*,{WSPATTERN}*{IDPATTERN}{WSPATTERN}*\\))')     # match ', owner)'

# Regex to match tagged mapping declarations
MAPPATTERN = re.compile(f'(?P<keep1>{NONIDSTART}mapping{WSPATTERN}*\\({WSPATTERN}*address{WSPATTERN}*)' # match 'mapping (address'
						f'(?P<repl>!{WSPATTERN}*{IDPATTERN})'                                           # match '!tag'
						f'(?P<keep2>{WSPATTERN}*=>{WSPATTERN}*)')                                       # match '=>'


def create_surrogate_string(instr: str):
	"""
	Preserve newlines and replace all other characters with spaces
	:return whitespace string with same length as instr and with the same line breaks
	"""
	return ''.join(['\n' if e == '\n' else ' ' for e in instr])


def replace_with_surrogate(code: str, search_pattern: re.Pattern, keep_end=True, surrogate_text: Optional[str]= None):
	while True:
		match = re.search(search_pattern, code)
		if match is None:
			return code

		rep_pattern = r'\g<keep1>' + \
					  (create_surrogate_string(match.groupdict()["repl"]) if surrogate_text is None else surrogate_text) + \
					  (r'\g<keep2>' if keep_end else '')

		code = re.sub(search_pattern, rep_pattern, code, count=1)


def fake_solidity_code(zkay_code: str):
	"""
	Returns the solidity code to which the given zkay_code corresponds when dropping all privacy features,
	while preserving original formatting
	"""

	code = zkay_code

	# Strip final
	code = replace_with_surrogate(code, FINAL_PATTERN)

	# Strip ownership annotations
	code = replace_with_surrogate(code, ATYPEPATTERN)

	# Strip map key tags
	code = replace_with_surrogate(code, MAPPATTERN)

	# Strip reveal expressions
	while True:
		match = re.search(REVEALPATTERN, code)
		if match is None:
			break
		code = re.sub(REVEALPATTERN, f'\\g<keep1>{create_surrogate_string(match.groupdict()["repl1"])}'
									 f'\\g<expr>{create_surrogate_string(match.groupdict()["repl2"])}', code, count=1)

	# 'all' should have been removed by first step
	assert re.search(ALLPATTERN, code) is None

	# Inject me address declaration (should be okay for type checking, maybe not for program analysis)
	# An alternative would be to replace me by msg.sender, but this would affect code length (error locations)
	code = replace_with_surrogate(code, CONTRACTDEFPATTERN, False, ME_DECL + '\n')

	return code
