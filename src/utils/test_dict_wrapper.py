
import unittest

from utils.dict_wrapper import DictWrapper


class TestDictWrapoper(unittest.TestCase):

	def test_indexing(self):
		d = DictWrapper()
		d['key'] = 'value'
		self.assertEqual(d['key'], 'value')

	def test_default(self):
		d = DictWrapper(default_value='value')
		self.assertEqual(d['key'], 'value')

	def test_list_key(self):
		d = DictWrapper()
		d[[]] = 'value'
		self.assertEqual(d[[]], 'value')

	def test_items(self):
		d = DictWrapper()
		d['key'] = 'value'
		d['key2'] = 'value2'
		items = list(d.items())
		self.assertEqual(items, [('key', 'value'), ('key2', 'value2')])
