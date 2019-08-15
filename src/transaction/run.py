from typing import Dict, Union, List
from random import randint

import my_logging
from bpl_ast.ast import ConstructorOrFunctionDefinition, TypeName, Expression, Parameter, SourceUnit, ConstructorDefinition
from compiler.privacy.compiler import compile_code, SolidityVisitor
from compiler.privacy.proof_helper import FromZok, ParameterCheck, FromSolidity
from compiler.zokrates.compiler import generate_proof
from my_logging.log_context import log_context
from transaction.encoding_helper import hash_ints_to_split_int
from transaction.simulate import Simulator
from utils.timer import time_measure


def get_runner(output_directory: str, code: str, contract_name: str, keys: Dict[str, int]):
	ast, compiler_information = compile_code(code, output_directory, None, True)
	s = Simulator()
	return Runner(ast, contract_name, compiler_information, keys, s)


class Runner:

	def __init__(
		self,
		ast: SourceUnit,
		contract_name: str,
		compiler_information: SolidityVisitor,
		keys: Dict[str, int],
		simulator: Simulator):

		self.ast = ast
		self.contract_name = contract_name
		self.compiler_information = compiler_information
		self.keys = keys
		self.randomness: Dict[Union[Expression, Parameter], int] = None
		self.simulator = simulator

	def get_function(self, f: str):
		return self.ast[self.contract_name][f]

	def run(
		self,
		f: ConstructorOrFunctionDefinition,
		me: str,
		parameters: List):
		# get compiler information
		h = self.compiler_information.function_helpers[f]

		# simulate original contract
		self.simulator.call(f, me, parameters)

		# prepare randomness
		self.randomness = {}

		# prepare relevant arguments
		args = []

		for p in f.parameters:
			args += [self.get_value(p)]

		# prepare proof
		my_logging.data('isPrivate', h.proof_parameter is not None)
		if h.proof_parameter:
			p = self.prepare_proof(f)

			p = p['proof']
			p = [p["A"][0], p["A"][1], p["B"][0][0], p["B"][0][1], p["B"][1][0], p["B"][1][1], p["C"][0], p["C"][1]]

			args += [p]

		precomputed = []
		for expr in h.precomputed_parameters:
			precomputed += [self.get_value(expr)]

		if len(precomputed) > 0:
			args += [precomputed]

		if isinstance(f, ConstructorDefinition):
			for c in self.compiler_information.used_contracts:
				args += [f'{c.state_variable_name}.address']

		return args

	def prepare_proof(self, f: ConstructorOrFunctionDefinition):
		proof_arguments = []
		public_arguments = []

		# get compiler information
		h = self.compiler_information.function_helpers[f]

		for proof_argument in h.zok.proof_helper.proof_arguments:
			ast = proof_argument.ast
			# we always need the value of the proof argument
			value = self.get_value(ast, want_int=True)
			proof_arguments += [value]
			public_arguments += [value]

			is_all = ast.annotated_type.privacy_annotation.is_all_expr()

			if isinstance(proof_argument, FromZok):
				if not is_all:
					key = self.get_key(ast)
					proof_arguments += [
						self.randomness[ast],
						key
					]
					public_arguments += [key]
			elif isinstance(proof_argument, ParameterCheck):
				assert not is_all
				key = self.get_key(ast)
				proof_arguments += [
					self.get_value(ast, want_int=True, want_plain=True),
					self.randomness[ast],
					key
				]
				public_arguments += [key]
			elif isinstance(proof_argument, FromSolidity):
				if not is_all:
					key = self.get_key(ast)
					proof_arguments += [key]

		# hash arguments and add them to zokrates arguments
		hash_ = hash_ints_to_split_int(public_arguments)
		proof_arguments += hash_

		# generate proof
		with time_measure('proofZokrates'):
			p = generate_proof(h.compiled_to_directory, proof_arguments)
		return p

	def get_randomness(self, ast: Union[Expression, Parameter]):
		if ast not in self.randomness:
			self.randomness[ast] = randint(100, 200)
		return self.randomness

	def get_value(self, ast: Union[Expression, Parameter], want_int=False, want_plain=False):
		value = self.simulator.values[ast]

		t = ast.annotated_type
		if t.privacy_annotation.is_all_expr() or want_plain:
			if t.type_name == TypeName.bool_type() and want_int:
				if value not in [True, False]:
					raise ValueError(f'Invalid boolean value: {value}')
				return 1 if value else 0
			else:
				return value
		else:
			if t.type_name == TypeName.bool_type():
				# encrypted bools are uints
				value = 1 if value else 0
			if not isinstance(value, int):
				msg = f'Currently, only integers and bools are supported as private arguments. Received: {value}'
				raise NotImplementedError(msg)
			assert isinstance(value, int)
			key = self.get_key(ast)
			self.get_randomness(ast)
			return value + key

	def get_key(self, ast: Union[Expression, Parameter]):
		assert not ast.annotated_type.privacy_annotation.is_all_expr()
		owner = self.simulator.owners[ast]
		return self.keys[owner]


# Convenience functions
def list_to_str(l: List, sep=', '):
	def my_str(x):
		if isinstance(x, bool):
			return '1' if x else '0'
		elif isinstance(x, List):
			l = [my_str(e) for e in x]
			return '[' + sep.join(l) + ']'
		elif isinstance(x, str):
			if is_hex(x):
				return f"'{x}'"
		return str(x)
	l = [my_str(e) for e in l]
	return sep.join(l)


def run_function(r: Runner, function_name: str, me: str, args: List):
	with time_measure('translateTransaction'):
		f = r.get_function(function_name)
		real_args = r.run(f, me, args)
		return real_args


def is_hex(s):
	try:
		int(s, 16)
		return True
	except ValueError:
		return False
