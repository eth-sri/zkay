import abc
import textwrap
from string import Formatter
from typing import List, Dict, Union, Optional

from zkay_ast.analysis.partition_state import PartitionState
from zkay_ast.visitor.visitor import AstVisitor


class AST:

	def __init__(self):
		# set later by parent setter
		self.parent: AST = None

		# Names accessible by AST nodes below this node.
		# Does not include names already listed by parents.
		# Maps strings (names) to Identifiers.
		#
		# set later by symbol table
		self.names: Dict[str, AST] = {}

		self.line = -1
		self.column = -1

	def children(self) -> List:
		ret = self.children_internal()
		ret = [e for e in ret if e is not None]
		return ret

	def children_internal(self) -> List:
		return []

	def code(self):
		v = CodeVisitor()
		s = v.visit(self)
		return s

	def __str__(self):
		return self.code()


class Identifier(AST):

	def __init__(self, name: str):
		super().__init__()
		self.name = name


class Expression(AST):

	@staticmethod
	def all_expr():
		return AllExpr()

	@staticmethod
	def me_expr():
		return MeExpr()

	def __init__(self):
		super().__init__()
		# set later by type checker
		self.annotated_type: AnnotatedTypeName = None
		# set by expression to statement
		self.statement: Statement = None

	def is_all_expr(self):
		return self == Expression.all_expr()

	def is_me_expr(self):
		return self == Expression.me_expr()

	def privacy_annotation_label(self):
		if isinstance(self, IdentifierExpr):
			if isinstance(self.target, Mapping):
				return self.target.instantiated_key.privacy_annotation_label()
			else:
				return self.target.idf
		elif self.is_all_expr():
			return self
		elif self.is_me_expr():
			return self
		else:
			return None

	def instanceof_data_type(self, expected):
		assert (isinstance(expected, TypeName))

		# check data type
		actual = self.annotated_type.type_name
		return expected == actual

	def instanceof(self, expected):
		"""

		:param expected:
		:return: True, False, or 'make-private'
		"""
		assert(isinstance(expected, AnnotatedTypeName))

		actual = self.annotated_type

		if not self.instanceof_data_type(expected.type_name):
			return False

		# check privacy type
		p_expected = expected.privacy_annotation.privacy_annotation_label()
		p_actual = actual.privacy_annotation.privacy_annotation_label()
		if not p_expected or not p_actual:
			return False
		else:
			if p_expected == p_actual:
				return True
			elif self.analysis is not None and self.analysis.same_partition(p_expected, p_actual):
				# analysis is not available, e.g., for state variables
				return True
			elif actual.privacy_annotation.is_all_expr():
				return 'make-private'
			else:
				return False

	@property
	def analysis(self):
		if self.statement is None:
			return None
		else:
			return self.statement.before_analysis


builtin_functions = {
	'index': '{}[{}]',
	'parenthesis': '({})',
	'ite': '{} ? {} : {}'
}

# arithmetic
arithmetic = {op: f'{{}} {op} {{}}' for op in ['**', '*', '/', '%', '+', '-']}
arithmetic.update({'sign+': '+{}', 'sign-': '-{}'})
# comparison
comp = {op: f'{{}} {op} {{}}' for op in ['<', '>', '<=', '>=']}
# equality
eq = {op: f'{{}} {op} {{}}' for op in ['==', '!=']}
# boolean operations
bop = {op: f'{{}} {op} {{}}' for op in ['&&', '||']}
bop['!'] = '!{}'

builtin_functions.update(arithmetic)
builtin_functions.update(comp)
builtin_functions.update(eq)
builtin_functions.update(bop)


class BuiltinFunction(Expression):

	def __init__(self, op: str):
		super().__init__()
		self.op = op
		# set later by type checker
		self.is_private: bool = False

		# input validation
		if op not in builtin_functions:
			raise ValueError(f'{op} is not a known built-in function')

	def format_string(self):
		return builtin_functions[self.op]

	def is_arithmetic(self):
		return self.op in arithmetic

	def is_neg_sign(self):
		return self.op == 'sign-'

	def is_comp(self):
		return self.op in comp

	def is_eq(self):
		return self.op in eq

	def is_bop(self):
		return self.op in bop

	def is_index(self):
		return self.op == 'index'

	def is_parenthesis(self):
		return self.op == 'parenthesis'

	def is_ite(self):
		return self.op == 'ite'

	def arity(self):
		return self.format_string().count('{}')

	def input_types(self):
		"""

		:return: None if the type is generic
		"""
		if self.is_arithmetic():
			t = TypeName.uint_type()
		elif self.is_comp():
			t = TypeName.uint_type()
		elif self.is_bop():
			t = TypeName.bool_type()
		else:
			# eq, index, parenthesis, ite
			return None

		return self.arity() * [t]

	def output_type(self):
		"""

		:return: None if the type is generic
		"""
		if self.is_arithmetic():
			return TypeName.uint_type()
		elif self.is_comp():
			return TypeName.bool_type()
		elif self.is_bop():
			return TypeName.bool_type()
		elif self.is_eq():
			return TypeName.bool_type()
		else:
			# index, parenthesis, ite
			return None

	def can_be_private(self):
		if self.op in arithmetic and self.op not in ['**', '/', '%']:
			return True
		elif self.op in comp:
			return True
		elif self.op in bop:
			return True
		elif self.op == 'parenthesis':
			return True
		else:
			# also returning False for equality, as this depends on the type
			return False


class FunctionCallExpr(Expression):

	def __init__(self, func: Expression, args: List[Expression]):
		super().__init__()
		self.func = func
		self.args = args

	def children_internal(self):
		return [self.func] + self.args


class MemberAccessExpr(Expression):
	def __init__(self, expr: Expression, member: Identifier):
		super().__init__()
		self.expr = expr
		self.member = member

	def children_internal(self) -> List:
		return [self.expr, self.member]


class AssignmentExpr(Expression):

	def __init__(self, lhs: Expression, rhs: Expression):
		super().__init__()
		self.lhs = lhs
		self.rhs = rhs

	def children_internal(self):
		return [self.lhs, self.rhs]


class BooleanLiteralExpr(Expression):

	def __init__(self, value: bool):
		super().__init__()
		self.value = value


class NumberLiteralExpr(Expression):

	def __init__(self, value: int):
		super().__init__()
		self.value = value


class IdentifierExpr(Expression):

	def __init__(self, idf: Identifier):
		super().__init__()
		self.idf = idf
		# set later by symbol table
		self.target: Union[
			VariableDeclaration,
			Parameter,
			FunctionDefinition,
			StateVariableDeclaration,
			ContractDefinition] = None

	def get_annotated_type(self):
		return self.target.annotated_type

	def children_internal(self):
		return [self.idf]


class MeExpr(Expression):

	def __eq__(self, other):
		return isinstance(other, MeExpr)

	def __hash__(self):
		return hash('me')


class AllExpr(Expression):

	def __eq__(self, other):
		return isinstance(other, AllExpr)

	def __hash__(self):
		return hash('all')


class ReclassifyExpr(Expression):

	def __init__(self, expr: Expression, privacy: Expression):
		super().__init__()
		self.expr = expr
		self.privacy = privacy

	def children_internal(self):
		return [self.expr, self.privacy]


class Statement(AST):

	def __init__(self):
		super().__init__()
		# set by alias analysis
		self.before_analysis: PartitionState = None
		self.after_analysis: PartitionState = None
		# set by parent setter
		self.function: ConstructorOrFunctionDefinition = None


class IfStatement(Statement):

	def __init__(self, condition: Expression, then_branch: Statement, else_branch: Statement):
		super().__init__()
		self.condition = condition
		self.then_branch = then_branch
		self.else_branch = else_branch

	def children_internal(self):
		return [self.condition, self.then_branch, self.else_branch]


class ReturnStatement(Statement):

	def __init__(self, expr: Expression):
		super().__init__()
		self.expr = expr

	def children_internal(self):
		return [self.expr]


class SimpleStatement(Statement):
	pass


class ExpressionStatement(SimpleStatement):

	def __init__(self, expr: Expression):
		super().__init__()
		self.expr = expr

	def children_internal(self):
		return [self.expr]


class RequireStatement(SimpleStatement):

	def __init__(self, condition: Expression):
		super().__init__()
		self.condition = condition

	def children_internal(self):
		return [self.condition]


class AssignmentStatement(SimpleStatement):

	def __init__(self, lhs: Expression, rhs: Expression):
		super().__init__()
		self.lhs = lhs
		self.rhs = rhs

	def children_internal(self):
		return [self.lhs, self.rhs]


class Block(Statement):

	def __init__(self, statements: List[Statement]):
		super().__init__()
		self.statements = statements

	def children_internal(self):
		return self.statements

	def __getitem__(self, key: int) -> Statement:
		return self.statements[key]


class TypeName(AST):
	__metaclass__ = abc.ABCMeta

	@staticmethod
	def bool_type():
		return ElementaryTypeName('bool')

	@staticmethod
	def uint_type():
		return ElementaryTypeName('uint')

	@staticmethod
	def address_type():
		return ElementaryTypeName('address')

	@staticmethod
	def void_type():
		return TupleType([])

	@staticmethod
	def address_payable_type():
		return PayableAddress()

	def is_primitive_type(self):
		return self == TypeName.bool_type() or self == TypeName.uint_type() or self == TypeName.address_type()

	def can_be_private(self):
		return self == TypeName.bool_type() or self == TypeName.uint_type()

	def __eq__(self, other):
		raise NotImplementedError()


class ElementaryTypeName(TypeName):

	def __init__(self, name: str):
		super().__init__()
		self.name = name

	def __eq__(self, other):
		if isinstance(other, ElementaryTypeName):
			return self.name == other.name
		return False


class UserDefinedTypeName(TypeName):

	def __init__(self, names: List[Identifier], definition=None):
		super().__init__()
		self.names = names
		self.definition = definition

	def __eq__(self, other):
		return isinstance(other, UserDefinedTypeName) and self.names == other.names


class AnnotatedTypeName(AST):

	def __init__(self, type_name: TypeName, privacy_annotation: Optional[Expression]):
		super().__init__()
		self.type_name = type_name
		self.had_privacy_annotation = privacy_annotation is not None
		if self.had_privacy_annotation:
			self.privacy_annotation = privacy_annotation
		else:
			self.privacy_annotation = AllExpr()

	def children_internal(self):
		return [self.type_name, self.privacy_annotation]

	def __eq__(self, other):
		if isinstance(other, AnnotatedTypeName):
			return self.type_name == other.type_name and self.privacy_annotation == other.privacy_annotation
		else:
			return False

	@staticmethod
	def uint_all():
		return AnnotatedTypeName(TypeName.uint_type(), Expression.all_expr())

	@staticmethod
	def bool_all():
		return AnnotatedTypeName(TypeName.bool_type(), Expression.all_expr())

	@staticmethod
	def address_all():
		return AnnotatedTypeName(TypeName.address_type(), Expression.all_expr())

	@staticmethod
	def void_all():
		return AnnotatedTypeName(TypeName.void_type(), Expression.all_expr())

	@staticmethod
	def all(type: TypeName):
		return AnnotatedTypeName(type, Expression.all_expr())

	@staticmethod
	def me(type: TypeName):
		return AnnotatedTypeName(type, Expression.me_expr())

	@staticmethod
	def array_all(value_type, *length: int):
		t = value_type
		for l in length:
			t = AnnotatedTypeName(Array(t, NumberLiteralExpr(l)), Expression.all_expr())
		return t


class Mapping(TypeName):

	def __init__(self, key_type: ElementaryTypeName, key_label: Identifier, value_type: AnnotatedTypeName):
		super().__init__()
		self.key_type = key_type
		self.key_label = key_label
		self.value_type = value_type
		# set by type checker: instantiation of the key by IndexExpr
		self.instantiated_key: Expression = None

	def children_internal(self):
		return [self.key_type, self.key_label, self.value_type]

	def __eq__(self, other):
		if isinstance(other, Mapping):
			return self.key_type == other.key_type and self.value_type == other.value_type
		else:
			return False


class PayableAddress(TypeName):
	def __eq__(self, other):
		return isinstance(other, PayableAddress)


class Array(TypeName):

	def __init__(self, value_type: AnnotatedTypeName, expr: Expression = None):
		super().__init__()
		self.value_type = value_type
		self.expr = expr

	def children_internal(self):
		return [self.value_type, self.expr]

	def __eq__(self, other):
		return self == other


class TupleType(TypeName):
	"""
	Does not appear in the syntax, but is necessary for type checking
	"""

	@staticmethod
	def ensure_tuple(t: AnnotatedTypeName):
		if isinstance(t.type_name, TupleType):
			return t
		else:
			return TupleType([t])

	def __init__(self, types: List[AnnotatedTypeName]):
		super().__init__()
		self.types = types

	def __len__(self):
		return len(self.types)

	def __iter__(self):
		"""
		Make this class iterable, by iterating over its types
		"""
		return self.types.__iter__()

	def __getitem__(self, i: int):
		return self.types[i]

	def check_component_wise(self, other, f):
		if isinstance(other, TupleType):
			if len(self) != len(other):
				return False
			else:
				for i in range(len(self)):
					if not f(self[i], other[i]):
						return False
				return True
		else:
			return False

	def perfect_privacy_match(self, other):
		def privacy_match(self: AnnotatedTypeName, other: AnnotatedTypeName):
			return self.privacy_annotation == other.privacy_annotation
		self.check_component_wise(other, privacy_match)

	def __eq__(self, other):
		return self.check_component_wise(other, lambda x, y: x == y)


class VariableDeclaration(AST):

	def __init__(self, keywords: List[str], annotated_type: AnnotatedTypeName, idf: Identifier):
		super().__init__()
		self.keywords = keywords
		self.annotated_type = annotated_type
		self.idf = idf

	def children_internal(self):
		return [self.annotated_type, self.idf]


class VariableDeclarationStatement(SimpleStatement):

	def __init__(self, variable_declaration: VariableDeclaration, expr: Optional[Expression]):
		"""

		:param variable_declaration:
		:param expr: can be None
		"""
		super().__init__()
		self.variable_declaration = variable_declaration
		self.expr = expr

	def children_internal(self):
		return [self.variable_declaration, self.expr]


class Parameter(AST):

	def __init__(
			self,
			keywords: List[str],
			annotated_type: AnnotatedTypeName,
			idf: Identifier,
			storage_location: Optional[str] = None):
		super().__init__()
		self.keywords = keywords
		self.annotated_type = annotated_type
		self.storage_location = storage_location
		self.idf = idf

	def children_internal(self):
		return [self.annotated_type, self.idf]


class FunctionTypeName(TypeName):
	def __init__(self, parameters: List[Parameter], modifiers: List[str], return_parameters: List[Parameter]):
		super().__init__()
		self.parameters = parameters
		self.modifiers = modifiers
		self.return_parameters = return_parameters

	def __eq__(self, other):
		return isinstance(other, FunctionTypeName) and self.parameters == other.parameters and \
			   self.modifiers == other.modifiers and self.return_parameters == other.return_parameters


class ConstructorOrFunctionDefinition(AST):

	def __init__(self, parameters: List[Parameter], modifiers: List[str], body: Block):
		super().__init__()
		self.parameters = parameters
		self.modifiers = modifiers
		self.body = body

		# specify parent type
		self.parent: ContractDefinition = None

	def children_internal(self):
		return self.parameters + [self.body]

	@property
	def name(self):
		if isinstance(self, ConstructorDefinition):
			return 'constructor'
		else:
			assert isinstance(self, FunctionDefinition)
			return self.idf.name


class FunctionDefinition(ConstructorOrFunctionDefinition):

	def __init__(
			self,
			idf: Identifier,
			parameters: List[Parameter],
			modifiers: List[str],
			return_parameters: List[Parameter],
			body: Block):
		super().__init__(parameters, modifiers, body)
		# set fields
		self.idf = idf
		self.return_parameters = return_parameters
		if return_parameters is None:
			self.return_parameters = []

		self.annotated_type: AnnotatedTypeName \
			= AnnotatedTypeName.all(FunctionTypeName(parameters, modifiers, return_parameters))

	def children_internal(self):
		return [self.idf] + self.parameters + self.return_parameters + [self.body]

	def get_return_type(self):
		if len(self.return_parameters) == 0:
			return None
		elif len(self.return_parameters) == 1:
			return self.return_parameters[0].annotated_type
		else:
			raise AstException(f'Multiple return types are not yet supported', self)

	def get_parameter_types(self):
		types = [p.annotated_type for p in self.parameters]
		return TupleType(types)


class ConstructorDefinition(ConstructorOrFunctionDefinition):

	def __init__(self, parameters: List[Parameter], modifiers: List[str], body: Block):
		super().__init__(parameters, modifiers, body)


class StateVariableDeclaration(AST):

	def __init__(self, annotated_type: AnnotatedTypeName, keywords: List[str], idf: Identifier, expr: Optional[Expression]):
		super().__init__()
		self.annotated_type = annotated_type
		self.keywords = keywords
		self.idf = idf
		self.expr = expr

	def children_internal(self):
		return [self.annotated_type, self.idf, self.expr]


class StructDefinition(AST):
	def __init__(self, idf: Identifier, members: List[VariableDeclaration]):
		super().__init__()
		self.idf = idf
		self.members = members


class ContractDefinition(AST):

	def __init__(
			self,
			idf: Identifier,
			state_variable_declarations: List[StateVariableDeclaration],
			constructor_definitions: List,
			function_definitions: List[FunctionDefinition]):
		super().__init__()
		self.idf = idf
		self.state_variable_declarations = state_variable_declarations
		self.constructor_definitions = constructor_definitions
		self.function_definitions = function_definitions

	def children_internal(self):
		return [self.idf] + self.state_variable_declarations + self.constructor_definitions + self.function_definitions

	def __getitem__(self, key: str):
		if key == 'constructor':
			if len(self.constructor_definitions) == 0:
				# return empty constructor
				c = ConstructorDefinition([], [], Block([]))
				c.parent = self
				return c
			elif len(self.constructor_definitions) == 1:
				return self.constructor_definitions[0]
			else:
				raise ValueError('Multiple constructors exist')
		else:
			d_identifier = self.names[key]
			return d_identifier.parent


class SourceUnit(AST):

	def __init__(self, pragma_directive: str, contracts: List[ContractDefinition]):
		super().__init__()
		self.pragma_directive = pragma_directive
		self.contracts = contracts

		self.original_code: List[str] = []

	def children_internal(self):
		return self.contracts

	def __getitem__(self, key: str):
		c_identifier = self.names[key]
		c = c_identifier.parent
		assert(isinstance(c, ContractDefinition))
		return c


# BUILTIN SPECIAL TYPE DEFINITIONS


class AddressMembers:
	# addr.balance: uint
	balance: AnnotatedTypeName = AnnotatedTypeName.uint_all()


class AddressPayableMembers(AddressMembers):
	# addr.send(uint) returns bool
	send: AnnotatedTypeName = AnnotatedTypeName.all(
		FunctionTypeName(
			parameters=[Parameter([], AnnotatedTypeName.all(TypeName.address_payable_type()), Identifier('')),
						Parameter([], AnnotatedTypeName.uint_all(), Identifier(''))],
			modifiers=[],
			return_parameters=[Parameter([], AnnotatedTypeName.bool_all(), Identifier(''))]
		)
	)

	# addr.transfer(uint)
	transfer: AnnotatedTypeName = AnnotatedTypeName.all(
		FunctionTypeName(
			parameters=[Parameter([], AnnotatedTypeName.all(TypeName.address_payable_type()), Identifier('')),
						Parameter([], AnnotatedTypeName.uint_all(), Identifier(''))],
			modifiers=[],
			return_parameters=[]
		)
	)


class GlobalDefs:
	gasleft: FunctionDefinition = FunctionDefinition(
		idf=Identifier('gasleft'),
		parameters=[],
		modifiers=[],
		return_parameters=[Parameter([], annotated_type=AnnotatedTypeName.uint_all(), idf=Identifier(''))],
		body=Block([])
	)
	gasleft.idf.parent = gasleft

	msg_struct: StructDefinition = StructDefinition(
		Identifier('<msg>'), [
			VariableDeclaration([], AnnotatedTypeName.all(TypeName.address_payable_type()), Identifier('sender')),
			VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('value')),
		]
	)

	block_struct: StructDefinition = StructDefinition(
		Identifier('<block>'), [
			VariableDeclaration([], AnnotatedTypeName.all(TypeName.address_payable_type()), Identifier('coinbase')),
			VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('difficulty')),
			VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('gaslimit')),
			VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('number')),
			VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('timestamp')),
		]
	)

	tx_struct: StructDefinition = StructDefinition(
		Identifier('<tx>'), [
			VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('gasprice')),
			VariableDeclaration([], AnnotatedTypeName.all(TypeName.address_payable_type()), Identifier('origin')),
		]
	)


class GlobalVars:
	msg: StateVariableDeclaration = StateVariableDeclaration(
		AnnotatedTypeName.all(UserDefinedTypeName([GlobalDefs.msg_struct.idf], GlobalDefs.msg_struct)), [],
		Identifier('msg'), None
	)
	msg.idf.parent = msg

	block: StateVariableDeclaration = StateVariableDeclaration(
		AnnotatedTypeName.all(UserDefinedTypeName([GlobalDefs.block_struct.idf], GlobalDefs.block_struct)), [],
		Identifier('block'), None
	)
	block.idf.parent = block

	tx: StateVariableDeclaration = StateVariableDeclaration(
		AnnotatedTypeName.all(UserDefinedTypeName([GlobalDefs.tx_struct.idf], GlobalDefs.tx_struct)), [],
		Identifier('tx'), None
	)
	tx.idf.parent = tx

	now: StateVariableDeclaration = StateVariableDeclaration(
		AnnotatedTypeName.uint_all(), [],
		Identifier('now'), None
	)
	now.idf.parent = now


# UTIL FUNCTIONS


def indent(s: str):
	return textwrap.indent(s, '\t')


# EXCEPTIONS


def get_code_error_msg(line: int, column: int, code: List[str], ctr: Optional[ContractDefinition] = None,
					   fct: Optional[FunctionDefinition] = None, stmt: Optional[Statement] = None):
	assert line <= len(code)

	# Print Location
	error_msg = f'Line: {line};{column}'
	if fct is not None:
		assert ctr is not None
		error_msg += f', in function \'{fct.name}\' of contract \'{ctr.idf.name}\''
	elif ctr is not None:
		error_msg += f', in contract \'{ctr.idf.name}\''
	error_msg += '\n'

	start_line = line if stmt is None else stmt.line
	for line in range(start_line, line + 1):
		# replace tabs with 4 spaces for consistent output
		orig_line: str = code[line - 1]
		orig_line = orig_line.replace('\t', '    ')
		error_msg += f'{orig_line}\n'

	affected_line: str = code[line - 1]
	loc_string = ''.join('----' if c == '\t' else '-' for c in affected_line[:column - 1])

	return f'{error_msg}{loc_string}/'


class AstException(Exception):
	"""
	Generic exception for errors in an AST
	"""

	def __init__(self, msg, ast):
		# Get surrounding statement
		if isinstance(ast, Expression):
			stmt = ast.statement
		elif isinstance(ast, Statement):
			stmt = ast
		else:
			stmt = None

		# Get surrounding function
		if stmt is not None:
			fct = stmt.function
		elif isinstance(ast, ConstructorOrFunctionDefinition):
			fct = ast
		else:
			fct = None

		# Get surrounding contract
		ctr = ast if fct is None else fct
		while ctr is not None and not isinstance(ctr, ContractDefinition):
			ctr = ctr.parent

		# Get source root
		root = ast if ctr is None else ctr
		while root is not None and not isinstance(root, SourceUnit):
			root = root.parent

		assert root is not None

		error_msg = get_code_error_msg(ast.line, ast.column, root.original_code, ctr, fct, stmt)

		super().__init__(f'\n{error_msg}\n{msg}')


# CODE GENERATION

class CodeVisitor(AstVisitor):

	def __init__(self, display_final=True):
		super().__init__('node-or-children')
		self.display_final = display_final

	def visit_list(self, l: List[Union[AST, str]], sep='\n'):
		if l is None:
			return 'None'

		def handle(e: Union[AST, str]):
			if isinstance(e, str):
				return e
			else:
				return self.visit(e)

		s = [handle(e) for e in l]
		s = sep.join(s)
		return s

	def visitAST(self, ast: AST):
		# should never be called
		raise NotImplementedError("Did not implement code generation for " + repr(ast))

	def visitIdentifier(self, ast: Identifier):
		return ast.name

	def visitFunctionCallExpr(self, ast: FunctionCallExpr):
		if isinstance(ast.func, BuiltinFunction):
			args = [self.visit(a) for a in ast.args]
			return ast.func.format_string().format(*args)
		else:
			first_arg = 1 if isinstance(ast.func, MemberAccessExpr) else 0
			f = self.visit(ast.func)
			a = self.visit_list(ast.args[first_arg:], ', ')
			return f'{f}({a})'

	def visitMemberAccessExpr(self, ast: MemberAccessExpr):
		return f'{self.visit(ast.expr)}.{self.visit(ast.member)}'

	def visitAssignmentExpr(self, ast: AssignmentExpr):
		lhs = self.visit(ast.lhs)
		rhs = self.visit(ast.rhs)
		return f'{lhs} = {rhs}'

	def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
		return str(ast.value).lower()

	def visitNumberLiteralExpr(self, ast: NumberLiteralExpr):
		return str(ast.value)

	def visitIdentifierExpr(self, ast: IdentifierExpr):
		return self.visit(ast.idf)

	def visitMeExpr(self, _: MeExpr):
		return 'me'

	def visitAllExpr(self, _: AllExpr):
		return 'all'

	def visitReclassifyExpr(self, ast: ReclassifyExpr):
		e = self.visit(ast.expr)
		p = self.visit(ast.privacy)
		return f'reveal({e}, {p})'

	def visitIfStatement(self, ast: IfStatement):
		c = self.visit(ast.condition)
		t = self.visit(ast.then_branch)
		ret = f'if ({c}) {t}'
		if ast.else_branch:
			e = self.visit(ast.else_branch)
			ret += f' else {e}'
		return ret

	def visitReturnStatement(self, ast: ReturnStatement):
		if ast.expr:
			e = self.visit(ast.expr)
			return f'return {e};'
		else:
			return 'return;'

	def visitExpressionStatement(self, ast: ExpressionStatement):
		return self.visit(ast.expr) + ';'

	def visitRequireStatement(self, ast: RequireStatement):
		c = self.visit(ast.condition)
		return f'require({c});'

	def visitAssignmentStatement(self, ast: AssignmentStatement):
		lhs = self.visit(ast.lhs)
		rhs = self.visit(ast.rhs)
		return f'{lhs} = {rhs};'

	def visitBlock(self, ast: Block):
		s = self.visit_list(ast.statements)
		s = indent(s)
		return f'{{\n{s}\n}}'

	def visitElementaryTypeName(self, ast: ElementaryTypeName):
		return ast.name

	def visitUserDefinedTypeName(self, ast: UserDefinedTypeName):
		return self.visit_list(ast.names, '.')

	def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
		t = self.visit(ast.type_name)
		p = self.visit(ast.privacy_annotation)
		if ast.had_privacy_annotation:
			return f'{t}@{p}'
		else:
			return t

	def visitMapping(self, ast: Mapping):
		k = self.visit(ast.key_type)
		label = '!' + self.visit(ast.key_label) if ast.key_label else ''
		v = self.visit(ast.value_type)
		return f"mapping({k}{label} => {v})"

	def visitPayableAddress(self, ast: PayableAddress):
		return "address payable"

	def visitArray(self, ast: Array):
		t = self.visit(ast.value_type)
		if ast.expr is not None:
			e = self.visit(ast.expr)
		else:
			e = ''
		return f'{t}[{e}]'

	def visitTupleType(self, ast: TupleType):
		s = self.visit_list(ast.types, ', ')
		return f'({s})'

	def visitVariableDeclaration(self, ast: VariableDeclaration):
		keywords = [k for k in ast.keywords if self.display_final or k != 'final']
		k = ' '.join(keywords)
		t = self.visit(ast.annotated_type)
		i = self.visit(ast.idf)
		return f'{k} {t} {i}'.strip()

	def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
		s = self.visit(ast.variable_declaration)
		if ast.expr:
			s += ' = ' + self.visit(ast.expr)
		s += ';'
		return s

	def visitParameter(self, ast: Parameter):
		if not self.display_final:
			f = None
		else:
			f = 'final' if 'final' in ast.keywords else None
		t = self.visit(ast.annotated_type)
		if ast.idf is None:
			i = None
		else:
			i = self.visit(ast.idf)

		description = [f, t, ast.storage_location, i]
		description = [d for d in description if d is not None]
		s = ' '.join(description)
		return s

	def visitFunctionDefinition(self, ast: FunctionDefinition):
		b = self.visit(ast.body)
		return self.function_definition_to_str(ast.idf, ast.parameters, ast.modifiers, ast.return_parameters, b)

	def function_definition_to_str(
			self,
			idf: Identifier,
			parameters: List[Union[Parameter, str]],
			modifiers: List[str],
			return_parameters: List[Parameter],
			body: str):
		if idf:
			i = self.visit(idf)
			definition = f'function {i}'
		else:
			definition = f'constructor'
		p = self.visit_list(parameters, ', ')
		m = ' '.join(modifiers)
		r = self.visit_list(return_parameters, ' ')
		if r != '':
			r = f'returns ({r})'

		f = f"{definition}({p}) {m} {r} {body}"
		return f

	def visitConstructorDefinition(self, ast: ConstructorDefinition):
		b = self.visit(ast.body)
		return self.function_definition_to_str(None, ast.parameters, ast.modifiers, [], b)

	def visitStateVariableDeclaration(self, ast: StateVariableDeclaration):
		keywords = [k for k in ast.keywords if self.display_final or k != 'final']
		f = 'final ' if 'final' in keywords else ''
		t = self.visit(ast.annotated_type)
		k = ' '.join([k for k in keywords if k != 'final'])
		if k != '':
			k = f'{k} '
		i = self.visit(ast.idf)
		ret = f"{f}{t} {k}{i}".strip()
		if ast.expr:
			ret += ' = ' + self.visit(ast.expr)
		return ret + ';'

	@staticmethod
	def contract_definition_to_str(
			idf: Identifier,
			state_vars: List[str],
			constructors: List[str],
			functions: List[str]):

		i = str(idf)
		state_vars = '\n'.join(state_vars)
		constructors = '\n\n'.join(constructors)
		functions = '\n\n'.join(functions)
		body = '\n\n'.join([state_vars, constructors, functions])
		body = indent(body)
		return f"contract {i} {{\n{body}\n}}"

	def visitContractDefinition(self, ast: ContractDefinition):
		state_vars = [self.visit(e) for e in ast.state_variable_declarations]
		constructors = [self.visit(e) for e in ast.constructor_definitions]
		functions = [self.visit(e) for e in ast.function_definitions]

		return self.contract_definition_to_str(
			ast.idf,
			state_vars,
			constructors,
			functions)

	def visitSourceUnit(self, ast: SourceUnit):
		p = ast.pragma_directive
		contracts = self.visit_list(ast.contracts)
		return f'{p}\n{contracts}'
