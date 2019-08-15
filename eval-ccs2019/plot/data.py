import os
import json

from utils.dict_wrapper import DictWrapper
import pandas as pd
# display all columns
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


script_dir = os.path.dirname(os.path.realpath(__file__))
examples_dir = os.path.join(script_dir, '..', 'examples')


def get_data():
	compiled_parser = Parser()
	scenario_parser = Parser()
	runner_log_parser = Parser(line_marker='#', context_keys=['contract', 'name', 'n'])
	for d in os.listdir(examples_dir):
		d = os.path.join(examples_dir, d)
		if os.path.isdir(d):
			if any(filename.endswith('.sol') for filename in os.listdir(d)):
				# get compiler logs
				compiled_log = os.path.join(d, 'compiled', 'compile_data.log')
				compiled_parser.add_context_logfile(compiled_log)
				# get transaction logs
				scenario_log = os.path.join(d, 'scenario', 'transactions_data.log')
				scenario_parser.add_context_logfile(scenario_log)
				# get runner logs
				runner_log = os.path.join(d, 'scenario', 'scenario.log')
				runner_log_parser.add_context_logfile(runner_log)

	# merge results
	data = compiled_parser + scenario_parser + runner_log_parser
	return data.get_tables()


class Parser:

	def __init__(self, line_marker=None, context_keys=None, allow_duplicates=False):
		default_d_context_value = DictWrapper()
		default_d_context_type = DictWrapper(default_value=default_d_context_value)
		self.d = DictWrapper(default_value=default_d_context_type)
		self.line_marker = line_marker
		self.context_keys = context_keys
		self.allow_duplicates = allow_duplicates

	def add_context_logfile(self, logfile):
		with open(logfile) as f:
			for line in f:
				if self.line_marker is not None:
					if not line.startswith(self.line_marker):
						continue
					line = line.replace(self.line_marker, '', 1)
				d = json.loads(line)
				self.add_all_by_context(d)

	def add_all_by_context(self, d):
		if self.context_keys:
			context_type = self.context_keys
			context_value = [d[k] for k in self.context_keys]
			payload = {k: v for k, v in d.items() if k not in self.context_keys}
		else:
			context_type = [c for c, _ in d['context']]
			context_value = [v for _, v in d['context']]
			payload = {d['key']: d['value']}

		for key, value in payload.items():
			if key in self.d[context_type][context_value] and not self.allow_duplicates:
				raise ValueError(f'Key {key} already present for context {context_value}')
			self.d[context_type][context_value][key] = value

	def __add__(self, other):
		assert isinstance(other, Parser)
		r = Parser()
		r.d = self.d + other.d
		return r

	def get_tables(self):
		tables = DictWrapper()
		for context_type, d_context_type in self.d.items():
			all_values = []
			for context_value, d_context_value in d_context_type.items():

				assert len(context_type) == len(context_value)
				row = {k: v for k, v in zip(context_type, context_value)}
				row.update({k: v for k, v in d_context_value.items()})
				all_values.append(row)

			tables[context_type] = pd.DataFrame(all_values)
		return tables


def main():
	p = get_data()
	for k, table in p.items():
		print(k)
		print(table)


if __name__ == '__main__':
	main()

