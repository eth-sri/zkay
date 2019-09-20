from shutil import copy
from typing import List, Dict, Optional
import os
import my_logging

from zkay_ast.ast import AST, CodeVisitor, AnnotatedTypeName, MeExpr, ReclassifyExpr, \
	FunctionDefinition, Parameter, RequireStatement, ExpressionStatement, SimpleStatement, \
	AssignmentStatement, Expression, Identifier, IdentifierExpr, indent, ReturnStatement, Mapping, \
	ConstructorDefinition, UserDefinedTypeName, ContractDefinition, StateVariableDeclaration, Block, \
	VariableDeclaration, VariableDeclarationStatement, TypeName, FunctionCallExpr, BuiltinFunction, BooleanLiteralExpr, \
	ConstructorOrFunctionDefinition
from zkay_ast.process_ast import get_processed_ast
from compiler.privacy.hash_function import hash_function
from compiler.privacy.proof_helper import ProofHelper, FromZok, ParameterCheck, FromSolidity
from compiler.privacy.tags import tag, helper_tag, param_tag
from compiler.privacy.used_contract import UsedContract
from compiler.zokrates.compiler import compile_zokrates, n_proof_arguments, get_work_dir
from my_logging.log_context import log_context
from utils.helpers import save_to_file, prepend_to_lines, lines_of_code

script_dir = os.path.dirname(os.path.realpath(__file__))
pki_contract_filename = 'pki.sol'
pki_contract_template = os.path.join(script_dir, pki_contract_filename)


def compile_ast(ast: AST, output_directory: str, output_file: Optional[str], simulate=False):
	"""

	Parameters:
	simulate (bool): Only simulate compilation to determine
	                 how to translate transactions
	"""
	v = SolidityVisitor(output_directory, simulate)
	s = v.visit(ast)

	my_logging.data('newLoc', lines_of_code(s))

	original_code = ast.code()
	original_code = prepend_to_lines(original_code, '// ')

	if simulate:
		return ast, v
	else:
		filename = save_to_file(output_directory, output_file, original_code + '\n\n' + s)
		copy(pki_contract_template, output_directory)
		return filename


def compile_code(code: str, output_directory: str, output_file: Optional[str], simulate=False):
	ast = get_processed_ast(code)

	return compile_ast(ast, output_directory, output_file, simulate)


class FunctionHelper:

	def __init__(self, v):
		assert isinstance(v, SolidityVisitor)

		self.return_variable: str = None

		# directory holding zokrates information (especially keys)
		self.compiled_to_directory: str = None

		self.n_temporary_variables = 0
		self.precomputed_parameters: List[Expression] = []
		self.proof_parameter = None
		self.verifier_contract_parameters = []

		self.zok = ZokratesVisitor(v, self)

	def get_next_temporary_variable(self):
		c = self.n_temporary_variables
		self.n_temporary_variables += 1
		return helper_tag, c

	def get_next_precomputed_parameter(self, expr: Expression):
		index = len(self.precomputed_parameters)
		self.precomputed_parameters += [expr]
		return param_tag, index

	def declare_temporary_variables(self, body: str):
		if self.n_temporary_variables > 0:
			body = f'uint[{self.n_temporary_variables}] memory {helper_tag};\n{body}'
		return body

	def add_return_variable(self, body: str):
		if self.return_variable is not None:
			body += f'\nreturn {self.return_variable};'
		return body

	def get_all_parameters(self, params: List):
		# make shallow copy of list
		params = list(params)

		# add proof parameter
		if self.proof_parameter:
			params += [self.proof_parameter]

		n = len(self.precomputed_parameters)
		if n > 0:
			params += [f'uint[{n}] memory {param_tag}']

		# add verifier contract parameters (only non-empty for constructor)
		params += self.verifier_contract_parameters

		return params

	def get_zok_arguments(self):
		return self.zok.proof_helper.zok_arguments


class SolidityVisitor(CodeVisitor):

	def __init__(self, output_directory: str, simulate=False):
		# do not display `final` keywords (`final` is not in Solidity fragment)
		super().__init__(False)

		# global properties
		self.output_directory = output_directory
		self.simulate = simulate

		# synthesized code
		self.pki_contract: UsedContract = None
		self.used_contracts: List[UsedContract] = []
		self.new_state_variables: List[StateVariableDeclaration] = []

		# per-function properties
		self.function_helpers: Dict[ConstructorOrFunctionDefinition, FunctionHelper] = {}
		self.function_helper: FunctionHelper = None

		# per-statement properties
		self.pre_simple_statement: List[str] = None

	def visitConstructorDefinition(self, ast: ConstructorDefinition):
		return self.handle_function_definition(ast)

	def visitFunctionDefinition(self, ast: FunctionDefinition):
		return self.handle_function_definition(ast)

	def visitFunctionCallExpr(self, ast: FunctionCallExpr):
		if isinstance(ast.func, BuiltinFunction):
			if ast.func.is_private:
				return self.function_helper.zok.from_zok(ast)
		return super().visitFunctionCallExpr(ast)

	def handle_function_definition(self, ast: ConstructorOrFunctionDefinition):
		with log_context('compileFunction', ast.name):

			self.function_helper = FunctionHelper(self)
			self.function_helpers[ast] = self.function_helper

			# check private parameters
			self.pre_simple_statement = []
			for p in ast.parameters:
				self.function_helper.zok.check_proper_encryption(p)
			body = '\n'.join(self.pre_simple_statement)

			# body
			body += self.visit_list(ast.body.statements)
			zok_code = self.function_helper.zok.code()

			# handle proofs
			my_logging.data('isPrivate', zok_code is not None)
			if zok_code is not None:
				if isinstance(ast, ConstructorDefinition):
					verifier_contract_name = 'Verify_constructor'
				elif isinstance(ast, FunctionDefinition):
					verifier_contract_name = f'Verify_{ast.idf.name}'
				else:
					raise ValueError(ast)

				if self.simulate:
					output_filename = None
					self.function_helper.compiled_to_directory = get_work_dir(self.output_directory, verifier_contract_name)
				else:
					my_logging.data('zokratesLoc', lines_of_code(zok_code))
					output_filename, d = compile_zokrates(zok_code, self.output_directory, name=verifier_contract_name)
					self.function_helper.compiled_to_directory = d

				verifier_contract_variable = verifier_contract_name + '_var'
				c = UsedContract(output_filename, verifier_contract_name, verifier_contract_variable)
				self.used_contracts += [c]

				# proof
				proof_type = AnnotatedTypeName.array_all(TypeName.uint_type(), n_proof_arguments)
				proof_name = verifier_contract_name + 'proof'
				proof_param = Parameter([], proof_type, Identifier(proof_name), 'memory')

				self.function_helper.proof_parameter = proof_param

				zok_arguments = self.function_helper.get_zok_arguments()
				body += f'\nuint256[] memory {tag}inputs = new uint256[]({len(zok_arguments)});\n'
				inputs = [f'{tag}inputs[{i}]={name};' for i, name in enumerate(zok_arguments)]
				body += '\n'.join(inputs)
				body += f'\nuint128[2] memory {tag}Hash = get_hash({tag}inputs);'
				body += f'\n{verifier_contract_variable}.check_verify({proof_name}, [{tag}Hash[0], {tag}Hash[1], uint(1)]);'

			body = self.function_helper.declare_temporary_variables(body)
			body = self.function_helper.add_return_variable(body)

			# handle constructors: add addresses of required contracts
			if isinstance(ast, ConstructorDefinition):
				for c in self.used_contracts:
					verifier_contract_parameter = c.state_variable_name + '_'
					t = AnnotatedTypeName(UserDefinedTypeName([Identifier(c.contract_name)]), Expression.all_expr())
					self.function_helper.verifier_contract_parameters += [f'{self.visit(t)} {verifier_contract_parameter}']
					body = f'{c.state_variable_name} = {verifier_contract_parameter};' + body
					decl = StateVariableDeclaration(t, [], Identifier(c.state_variable_name), None)
					self.new_state_variables += [decl]

			# wrap up
			body = indent(body)
			body = f'{{\n{body}\n}}'

			# prepare arguments for generating code
			if isinstance(ast, ConstructorDefinition):
				idf = None
				return_parameters = []
			elif isinstance(ast, FunctionDefinition):
				idf = ast.idf
				return_parameters = ast.return_parameters
			else:
				raise ValueError(ast)

			# determine parameters
			params = self.function_helper.get_all_parameters(ast.parameters)

			# record number of switches between zokrates and solidity
			my_logging.data('nCrosses', len(self.function_helper.zok.proof_helper.proof_arguments))

			return super().function_definition_to_str(idf, params, ast.modifiers, return_parameters, body)

	def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
		# only display data type, not privacy annotation
		t = self.visit(ast.type_name)
		if ast.privacy_annotation.is_all_expr():
			return t
		else:
			return TypeName.uint_type().code()

	def visitMapping(self, ast: Mapping):
		k = self.visit(ast.key_type)
		v = self.visit(ast.value_type)
		return f"mapping({k} => {v})"

	def visitMeExpr(self, _: MeExpr):
		return 'msg.sender'

	def visitReclassifyExpr(self, ast: ReclassifyExpr):
		# take result from zokrates
		r = self.function_helper.zok.from_zok(ast)
		if ast.annotated_type.type_name == TypeName.bool_type() and ast.annotated_type.privacy_annotation.is_all_expr():
			return f'{r} == 1'
		else:
			return r

	def handleSimpleStatement(self, ast: SimpleStatement, f):
		self.pre_simple_statement = []
		code = f(ast)
		statements = '\n'.join(self.pre_simple_statement + [code])
		return statements

	def visitExpressionStatement(self, ast: ExpressionStatement):
		return self.handleSimpleStatement(ast, super().visitExpressionStatement)

	def visitRequireStatement(self, ast: RequireStatement):
		return self.handleSimpleStatement(ast, super().visitRequireStatement)

	def visitAssignmentStatement(self, ast: AssignmentStatement):
		return self.handleSimpleStatement(ast, super().visitAssignmentStatement)

	def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
		return self.handleSimpleStatement(ast, super().visitVariableDeclarationStatement)

	def visitReturnStatement(self, ast: ReturnStatement):
		if ast.expr is None:
			return 'return;'
		else:
			self.function_helper.return_variable = f'{tag}Return'

			d = VariableDeclaration([], ast.expr.annotated_type, Identifier(self.function_helper.return_variable))
			d = VariableDeclarationStatement(d, ast.expr)

			# "return" will be emitted when handling function declaration
			return self.visit(d)

	def visitContractDefinition(self, ast: ContractDefinition):
		with log_context('contract', ast.idf.name):
			functions = [self.visit(e) for e in ast.function_definitions]

			# constructors
			if len(ast.constructor_definitions) == 0:
				# add an empty constructor
				c = ConstructorDefinition([], ['public'], Block([]))
				c.parent = ast
				ast.constructor_definitions = [c]
			constructor_definitions = ast.constructor_definitions
			constructors = [self.visit(e) for e in constructor_definitions]

			# state variables
			decl = self.new_state_variables + ast.state_variable_declarations
			state_vars = [self.visit(e) for e in decl]

			# imports
			imported_filenames = [c.filename for c in self.used_contracts]
			imports = '\n'.join([f'import "./{f}";' for f in imported_filenames])

			# add hash function
			functions += [hash_function]

			# final string generation
			contract = self.contract_definition_to_str(
				ast.idf,
				state_vars,
				constructors,
				functions)
			return f'\n{imports}\n\n{contract}'


zok_helpers = """
def dec(field msg, field key) -> (field):
	return msg - key

def enc(field msg, field R, field key) -> (field):
	// artificial constraints ensuring every variable is used
	field impossible = if R == 0 && R == 1 then 1 else 0 fi
	impossible == 0
	return msg + key

import "hashes/sha256/512bitPacked.code" as sha256packed

def checkHash(field[$NINPUTS] inputs, field[2] expectedHash) -> (field):
	field[2] hash = [0, inputs[0]]
	for field i in 1..$NINPUTS do
		field[4] toHash = [hash[0], hash[1], 0, inputs[i]]
		hash = sha256packed(toHash)
	endfor
	
	hash[0] == expectedHash[0]
	hash[1] == expectedHash[1]
	return 1
"""


class ZokratesVisitor(CodeVisitor):

	def __init__(self, sol: SolidityVisitor, function_helper: FunctionHelper):
		super().__init__(False)
		self.sol = sol
		self.function_helper = function_helper
		self.proof_helper = ProofHelper()

		self.want_bool = False

	def code(self):
		if len(self.proof_helper.statements) > 0:
			inputs = ", ".join(self.proof_helper.public_params)
			statements = [f'1 == checkHash([{inputs}], [inputHash0, inputHash1])'] + self.proof_helper.statements + ['return 1']
			s = '\n'.join(statements)
			s = indent(s)
		else:
			return None

		n_public_params = len(self.proof_helper.public_params)

		args = ', '.join(self.proof_helper.zok_params + ['field inputHash0', 'field inputHash1'])
		my_logging.data('nPublicParams', n_public_params)
		docs = '\n'.join([f'{n}: {d}' for n, d in self.proof_helper.param_docs])
		docs = prepend_to_lines(docs, '// ')

		adjusted_zok_helpers = zok_helpers.replace('$NINPUTS', str(n_public_params))
		return f'{adjusted_zok_helpers}\n\n{docs}\ndef main({args}) -> (field):\n{s}'

	def from_zok(self, ast: Expression):
		with WantBool(self, False):
			expr = self.visit(ast)

		is_all = ast.annotated_type.privacy_annotation.is_all_expr()

		# add to function parameter
		t, c = self.function_helper.get_next_precomputed_parameter(ast)

		# add to zokrates argument
		zok_argument = f'{t}[{c}]'
		self.proof_helper.zok_arguments += [zok_argument]
		if not is_all:
			pki = self.ensure_pki()
			owner = ast.annotated_type.privacy_annotation.privacy_annotation_label()
			self.proof_helper.zok_arguments += [f'{pki}.getPk({self.sol.visit(owner)})']

		# add to zokrates parameter
		zok_parameter = f'{t}{c}'
		self.proof_helper.add_public_param(zok_parameter, ast)

		# add to zokrates arguments & emit zokrates code
		if is_all:
			# add check
			self.proof_helper.statements += [f'{zok_parameter} == {expr}']
		else:
			# add to zokrates arguments
			randomness = self.proof_helper.add_randomness(zok_parameter)
			key = f'{zok_parameter}PK'
			self.proof_helper.add_public_param(key, ast)

			# add check
			self.proof_helper.statements += [
				f'field {zok_parameter}Dec = {expr}',
				f'{zok_parameter} == enc({zok_parameter}Dec, {randomness}, {key})'
			]

		# add to zokrates proof argument
		self.proof_helper.proof_arguments += [FromZok(ast)]

		# return expression in solidity
		return zok_argument

	def ensure_pki(self):
		contract_name = 'PublicKeyInfrastructure'
		pki = f'{tag}{contract_name}'
		if self.sol.pki_contract is None:
			self.sol.pki_contract = UsedContract(pki_contract_filename, contract_name, pki)
			self.sol.used_contracts += [self.sol.pki_contract]
		return pki

	def check_proper_encryption(self, p: Parameter):
		if p.annotated_type.privacy_annotation.is_all_expr():
			# no check necessary
			pass
		else:
			# prepare zokrates argument
			t, c = self.function_helper.get_next_temporary_variable()
			helper_var_name = f'{t}[{c}]'
			self.sol.pre_simple_statement += [f'{helper_var_name} = {p.idf};']

			# add to zokrates argument
			pki = self.ensure_pki()
			owner = p.annotated_type.privacy_annotation.privacy_annotation_label()
			self.proof_helper.zok_arguments += [helper_var_name, f'{pki}.getPk({self.sol.visit(owner)})']

			# add to zokrates parameter
			parameter_var_name = f'{t}{c}'
			self.proof_helper.add_public_param(parameter_var_name, p)
			value = self.proof_helper.add_value(parameter_var_name)
			randomness = self.proof_helper.add_randomness(parameter_var_name)
			key = f'{parameter_var_name}PK'
			self.proof_helper.add_public_param(key, p)

			# add to zokrates code
			self.proof_helper.statements += [f'{parameter_var_name} == enc({value}, {randomness}, {key})']

			# add to zokrates proof argument
			self.proof_helper.proof_arguments += [ParameterCheck(p)]

	def _from_solidity(self, ast: Expression):
		assert (ast.annotated_type.type_name.can_be_private())

		# prepare zokrates argument
		t, c = self.function_helper.get_next_temporary_variable()
		helper_var_name = f'{t}[{c}]'
		sol_expr = self.sol.visit(ast)
		self.sol.pre_simple_statement += [f'{helper_var_name} = {sol_expr};']

		# add to zokrates argument
		self.proof_helper.zok_arguments += [helper_var_name]

		# add to zokrates parameter, prepare expression holding `ast`
		parameter_var_name = f'{t}{c}'
		self.proof_helper.add_public_param(parameter_var_name, ast)
		if ast.annotated_type.privacy_annotation.is_all_expr():
			ret = parameter_var_name
		else:
			key = self.proof_helper.add_private_key(parameter_var_name)
			ret = f'dec({parameter_var_name}, {key})'

		# add to zokrates proof argument
		self.proof_helper.proof_arguments += [FromSolidity(ast)]

		# return zokrates expression holding ast
		return ret

	def from_solidity(self, ast: Expression):
		v = self._from_solidity(ast)
		return self.ensure_bool_or_int(v, False)

	def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
		return self.ensure_bool_or_int('1' if ast.value else '0', False)

	def visitIdentifierExpr(self, ast: IdentifierExpr):
		return self.from_solidity(ast)

	@staticmethod
	def bool_to_int(e: str):
		return f'if {e} then 1 else 0 fi'

	@staticmethod
	def int_to_bool(e: str):
		return f'{e} == 1'

	def ensure_bool_or_int(self, e: str, is_bool: bool):
		if self.want_bool and is_bool:
			return e
		elif self.want_bool and not is_bool:
			return self.int_to_bool(e)
		elif not self.want_bool and is_bool:
			return self.bool_to_int(e)
		elif not self.want_bool and not is_bool:
			return e
		assert False

	def visitFunctionCallExpr(self, ast: FunctionCallExpr):
		if isinstance(ast.func, BuiltinFunction):
			if not ast.func.is_private:
				return self.from_solidity(ast)
			elif ast.func.op == 'ite':
				with WantBool(self, True):
					cond = self.visit(ast.args[0])
				t = self.visit(ast.args[1])
				e = self.visit(ast.args[2])
				# bool vs int correct because self.want_bool is handled recursively
				return f'if {cond} then {t} else {e} fi'
			elif ast.func.is_bop():
				with WantBool(self, True):
					args = [self.visit(arg) for arg in ast.args]
					# add parenthesis
					args = [f'({a})' for a in args]
				e = ast.func.format_string().format(*args)
				return self.ensure_bool_or_int(e, True)
			elif ast.func.op == '!=':
				args = [self.visit(arg) for arg in ast.args]
				e = f'! ({args[0]} == {args[1]})'
				return self.ensure_bool_or_int(e, True)
			elif ast.func.op == '==' or ast.func.is_comp():
				with WantBool(self, False):
					e = super().visitFunctionCallExpr(ast)
				return self.ensure_bool_or_int(e, True)

		return super().visitFunctionCallExpr(ast)

	def visitReclassifyExpr(self, ast: ReclassifyExpr):
		# stay within zokrates, even if sub-expression is public
		# we will only step out when we hit an operation zokrates cannot handle
		return self.visit(ast.expr)


class WantBool:
	def __init__(self, v: ZokratesVisitor, want_bool: bool):
		self.v = v
		self.want_bool = want_bool

	def __enter__(self):
		self.old = self.v.want_bool
		self.v.want_bool = self.want_bool

	def __exit__(self, t, value, traceback):
		self.v.want_bool = self.old
