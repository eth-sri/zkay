
# Use regular expression replacements to strip all zkay specific language features
# (so that code can be passed to solc for type checking)
# TODO? currently text inside comments is also processed

import re

me_decl = ' address private me = msg.sender;'

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
CONTRACTDEFPATTERN = re.compile(f'(?P<keep>{NONIDSTART}contract{WSPATTERN}*{IDPATTERN}{WSPATTERN}*{"{"}(?P<decl>[^\n]*))\n')

# Regex to match annotated types
ATYPEPATTERN = re.compile(f'(?P<keep1>{NONIDSTART}{TPATTERN}{WSPATTERN}*)' # match type
						  f'(?P<repl>@{WSPATTERN}*{IDPATTERN})'             # match @owner
						  f'(?P<keep2>{NONIDEND})')                         # match after owner

# Regex to match 'final' keyword
FINAL_PATTERN = re.compile(f'(?P<keep1>{NONIDSTART})' # match before all
						f'(?P<repl>final)'           # match 'final'
						f'(?P<keep2>{NONIDEND})')  # match after all

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


def fake_solidity_code(zkay_code: str):
	"""
	Returns the solidity code to which the given zkay_code corresponds when dropping all privacy features,
	while preserving original formatting
	"""

	code = zkay_code

	# Strip final
	while True:
		match = re.search(FINAL_PATTERN, code)
		if match is None:
			break
		code = re.sub(FINAL_PATTERN, f'\\g<keep1>{create_surrogate_string(match.groupdict()["repl"])}\\g<keep2>',
					  code, count=1)

	# Strip ownership annotations
	while True:
		match = re.search(ATYPEPATTERN, code)
		if match is None:
			break
		code = re.sub(ATYPEPATTERN, f'\\g<keep1>{create_surrogate_string(match.groupdict()["repl"])}\\g<keep2>',
					  code, count=1)

	# Strip map key tags
	while True:
		match = re.search(MAPPATTERN, code)
		if match is None:
			break
		code = re.sub(MAPPATTERN, f'\\g<keep1>{create_surrogate_string(match.groupdict()["repl"])}\\g<keep2>',
					  code, count=1)

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
	while True:
		match = re.search(CONTRACTDEFPATTERN, code)
		if match is None or ('decl' in match.groupdict().keys() and me_decl in match.groupdict()['decl']):
			break
		code = re.sub(CONTRACTDEFPATTERN, f'\\g<keep>{me_decl}\n',
					  code, count=1)

	return code
