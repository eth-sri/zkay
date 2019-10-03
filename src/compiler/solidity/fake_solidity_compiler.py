
# Use regular expression replacements to strip all zkay specific language features
# (so that code can be passed to solc for type checking)

import re

# Whitespace
WSPATTERN = r'[ \t\r\n\u000C]'

# Identifier
IDPATTERN = r'[a-zA-Z\$_][a-zA-Z\$_]*'

# Type
BTPATTERN = r'(?:address|bool|uint)'
ETPATTERN = f'(?:{BTPATTERN}'

# Match what is adjacent to word (type, identifier, keyword)
NONIDSTART = r'(?:[^\w]|^)'
NONIDEND = r'(?:[^\w]|$)'

# Regex to match annotated types
ATYPEPATTERN = re.compile(f'(?P<keep1>{NONIDSTART}{BTPATTERN}{WSPATTERN}*)'
						  f'(?P<repl>@{WSPATTERN}*{IDPATTERN})'
						  f'(?P<keep2>{NONIDEND})')

# Regex to match all keyword
ALLPATTERN = re.compile(f'(?P<keep1>{NONIDSTART})'
						f'(?P<repl>all)'
						f'(?P<keep2>{NONIDEND})')

# Regex to match reveal expressions
REVEALPATTERN = re.compile(f'(?P<keep1>{NONIDSTART})(?P<repl1>reveal{WSPATTERN}*\\({WSPATTERN}*)'
						   f'(?P<expr>[^°]*)'
						   f'(?P<repl2>{WSPATTERN}*,{WSPATTERN}*{IDPATTERN}{WSPATTERN}*\\))')

# Regex to match tagged mapping declarations
MAPPATTERN = re.compile(f'(?P<keep1>{NONIDSTART}mapping{WSPATTERN}*\\({WSPATTERN}*address{WSPATTERN}*)'
						f'(?P<repl>!{WSPATTERN}*{IDPATTERN})'
						f'(?P<keep2>{WSPATTERN}*=>{WSPATTERN}*)')


def create_surrogate_string(instr: str):
	'''
	Preserve newlines and replace all other characters with spaces
	:return whitespace string with same length as instr and with the same line breaks
	'''
	return ''.join(['\n' if e == '\n' else ' ' for e in instr])


def fake_solidity_code(zkay_code: str):
	'''
	Returns the solidity code to which the given zkay_code corresponds when dropping all privacy features,
	while preserving original formatting
	'''

	code = zkay_code

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
	match = re.search(ALLPATTERN, code)
	assert match is None

	return code
