from typing import List
from copy import copy


class DictWrapper:

	def __init__(self, default_value=None):
		self.d = {}
		self._keys = {}
		self.default_value = default_value

	def items(self):
		for k, v in self.d.items():
			yield self._keys[k], v

	def get_key(self, key):
		if isinstance(key, List):
			ret = str(key)
		else:
			ret = key
		self._keys[ret] = key
		return ret

	def keys(self):
		return self._keys.values()

	def values(self):
		return self.d.values()

	def print_items(self):
		print('=====START OF DICT=====')
		for k, v in self.items():
			print(f'{str(k)}:')
			print(v)
		print('=====END OF DICT=====')

	def __getitem__(self, item):
		item = self.get_key(item)
		self.d.setdefault(item, copy(self.default_value))
		return self.d[item]

	def __setitem__(self, key, value):
		key = self.get_key(key)
		self.d[key] = value

	def __eq__(self, other):
		if isinstance(other, DictWrapper):
			return self.d == other.d
		else:
			return False

	def __copy__(self):
		r = DictWrapper()
		r.d = copy(self.d)
		r._keys = copy(self._keys)
		r.default_value = copy(self.default_value)
		return r

	def __repr__(self):
		return repr(self.d)

	def __contains__(self, item):
		key = self.get_key(item)
		return key in self.d

	def __add__(self, other):
		# check consistency
		assert isinstance(other, DictWrapper)
		if self.default_value != other.default_value:
			raise ValueError(f'Inconsistent default values: {self.default_value} vs {other.default_value}')
		for hashed_key, key in self._keys.items():
			if hashed_key in other._keys:
				assert self._keys[hashed_key] == other._keys[hashed_key]

		# create result
		r = DictWrapper(self.default_value)
		# merge keys
		r._keys.update(self._keys)
		r._keys.update(other._keys)

		# insert items from d
		r.d.update(self.d)

		# insert items from other
		for k, v in other.items():
			if k not in r:
				r[k] = v
			else:
				if isinstance(v, List) and isinstance(r[k], List):
					r[k] += v
				if isinstance(v, DictWrapper) and isinstance(r[k], DictWrapper):
					r[k] += v
				else:
					raise NotImplementedError()
		return r

	def __iadd__(self, other):
		return self + other
