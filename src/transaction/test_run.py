import os
import shutil
from unittest import TestCase


from compiler.privacy.compiler import compile_code
from examples.examples import addition, private_addition, power_grid
from transaction.run import get_runner

script_dir = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(script_dir, 'output')


def get_directory(name: str):
	d = os.path.join(output_dir, name)

	if os.path.isdir(d):
		shutil.rmtree(d)
	os.mkdir(d)

	return d


class TestRunner(TestCase):

	def test_addition(self):
		name = 'Addition'

		c = addition.code()
		d = get_directory(name)

		# compile
		compile_code(c, d, name)

		r = get_runner(d, c, name, {})
		f = r.get_function('f')

		args = r.run(f, 'me', [1, 2])

		self.assertEqual(args, [1, 2])

	def test_private_addition(self):
		name = 'PrivateAddition'

		c = private_addition.code()
		d = get_directory(name)

		# compile
		compile_code(c, d, name)

		r = get_runner(d, c, name, {'me': 10})

		f = r.get_function('constructor')
		args = r.run(f, 'me', [])
		addresses = [
			'genPublicKeyInfrastructure.address',
			'Verify_set_var.address',
			'Verify_f_var.address'
		]
		self.assertEqual(args, addresses)

		# set x
		f = r.get_function('set')
		args = r.run(f, 'me', [0])
		self.check_and_remove_proof(args, 1)
		self.assertEqual(args, [0, [10]])

		f = r.get_function('f')
		args = r.run(f, 'me', [5])
		self.check_and_remove_proof(args, 1)
		self.assertEqual(args, [5, [15]])

	def test_power_grid(self):
		name = 'PowerGrid'

		c = power_grid.code()
		d = get_directory(name)

		# compile
		compile_code(c, d, name)

		r = get_runner(d, c, name, {'me': 10})

		f = r.get_function('constructor')
		args = r.run(f, 'me', [])
		addresses = [
			'genPublicKeyInfrastructure.address',
			'Verify_init_var.address',
			'Verify_register_consumed_var.address',
			'Verify_declare_total_var.address'
		]
		self.assertEqual(args, addresses)

		f = r.get_function('init')
		args = r.run(f, 'me', [])
		self.check_and_remove_proof(args, 0)
		self.assertEqual(args, [[10]])

		f = r.get_function('register_consumed')
		args = r.run(f, 'me', [25])
		self.check_and_remove_proof(args, 1)
		self.assertEqual(args, [35, [35]])

		f = r.get_function('declare_total')
		args = r.run(f, 'me', [])
		self.check_and_remove_proof(args, 0)
		self.assertEqual(args, [[35]])

	def check_and_remove_proof(self, args, pos):
		self.assertEqual(len(args[pos]), 8)
		del args[pos]
