import os
import pandas as pd
import numpy as np
from plot.data import get_data
import matplotlib.pyplot as plt
import matplotlib

from plot.cost import add_cost_axis, set_n_ticks

# enable latex formatting
plt.rc('text', usetex=True)
plt.rc('font', family='serif')
matplotlib.rcParams['mathtext.fontset'] = 'custom'
matplotlib.rcParams['mathtext.rm'] = 'LibertineLF'


script_dir = os.path.dirname(os.path.realpath(__file__))


def flatten(l):
	return [item for sublist in l for item in sublist]


def get_per_function(p):
	per_function = p[['inputfile', 'contract', 'compileFunction']]
	assert isinstance(per_function, pd.DataFrame)

	# handle formatting issues
	per_function = per_function.fillna(0)
	to_int = ['isPrivate', 'verifierLoc', 'zokratesLoc', 'nPublicParams']
	per_function[to_int] = per_function[to_int].astype(int)

	return per_function


def get_per_transaction(p):
	per_transaction = p[['inputfileTx', 'nCalls', 'runFunction']]
	per_transaction.rename(index=str, columns={'inputfileTx': 'inputfile'}, inplace=True)
	per_transaction = per_transaction.fillna(0)
	per_transaction = per_transaction.assign(nTransactions=1)
	per_transaction['isPrivate'] = per_transaction['isPrivate'].astype(int)
	per_transaction.rename(index=str, columns={'isPrivate': 'nPrivateTx'}, inplace=True)
	per_transaction['zokratesTranslateFraction'] = per_transaction['proofZokrates'] / per_transaction['translateTransaction']
	return per_transaction


def get_per_file(p):
	per_file = p[['inputfile']]
	assert isinstance(per_file, pd.DataFrame)

	# add aggregated function information
	per_function = get_per_function(p)
	# drop irrelevant columns
	per_function.drop(columns=['compileFunction', 'nPublicParams'], inplace=True)
	per_function = per_function.assign(nFunctions=1)
	function_sum = per_function.groupby(['inputfile', 'contract']).sum()
	function_sum.reset_index(level=['contract'], inplace=True)
	function_sum.rename(index=str, columns={'isPrivate': 'nPrivateFunctions'}, inplace=True)

	per_file = per_file.merge(function_sum, on='inputfile')

	# add total new lines
	per_file['totalNewLoc'] = per_file['newLoc'] + per_file['zokratesLoc']

	# add aggregated transaction information
	per_transaction = get_per_transaction(p)
	transaction_overview = per_transaction.groupby(['inputfile']).sum()
	transaction_overview = transaction_overview[['nPrivateTx', 'nTransactions']]
	per_file = per_file.merge(transaction_overview, on='inputfile')

	# compute zokrates fraction
	per_file['compileZokratesFraction'] = per_file['compileZokrates'] / per_file['compileFull']

	per_file.sort_values(by=['contract'], inplace=True)

	return per_file


def get_per_contract_stats(p):
	per_file = get_per_file(p)
	per_file.drop(columns=['inputfile'], inplace=True)

	stats = per_file.copy()
	stats['blowupLoc'] = stats['totalNewLoc'] / stats['originalLoc']
	stats['nCrossesPerLoc'] = stats['nCrosses'] / stats['originalLoc']
	d = {'originalLoc': 'mean', 'totalNewLoc': 'mean', 'blowupLoc': 'mean', 'nCrossesPerLoc': 'mean'}
	agg = aggregate_columns(stats, d)

	return per_file, agg


def aggregate_columns(df, d):
	agg = df.agg(d)
	agg.rename({k: f'{k} ({v})' for k, v in d.items()}, inplace=True)
	return agg


def get_compile_time_stats(p):
	per_file = get_per_file(p)
	d = {'compileFull': 'max', 'compileZokratesFraction': 'min'}
	agg = aggregate_columns(per_file, d)
	return agg


def get_transaction_time_stats(p):
	per_transaction = get_per_transaction(p)
	max_transaction = aggregate_columns(per_transaction, {'translateTransaction': 'max'})
	per_transaction = per_transaction[per_transaction['proofZokrates'] > 0]
	avg_transaction = aggregate_columns(per_transaction, {'zokratesTranslateFraction': 'min'})
	return pd.concat([max_transaction, avg_transaction])


def get_transaction_runs(p, only_private=False):
	transaction_runs = p[['contract', 'name', 'n']]

	# rename constructors
	constructors = transaction_runs['contract'] == transaction_runs['name']
	transaction_runs.loc[constructors, 'name'] = 'constructor'

	# add information
	per_function = get_per_function(p)
	per_function.rename(index=str, columns={'compileFunction': 'name'}, inplace=True)
	transaction_runs = transaction_runs.merge(per_function, on=['name', 'contract'], how='left')

	if only_private:
		# remove non-private (also removes deployment of prover contracts)
		transaction_runs = transaction_runs[transaction_runs['isPrivate'] == 1]

	# add phase numbers
	transaction_runs['phase'] = 3
	transaction_runs.loc[transaction_runs['type'] == 'deploy', 'phase'] = 1
	transaction_runs.loc[transaction_runs['name'] == 'announcePk', 'phase'] = 1
	transaction_runs.loc[transaction_runs['name'] == 'constructor', 'phase'] = 2
	transaction_runs.loc[transaction_runs['name'].str.contains('Verify_'), 'phase'] = 2

	# sort by phase
	transaction_runs.sort_values('phase', inplace=True, kind='mergesort')

	# rename verifiers
	def rename(name):
		if 'Verify_' in name:
			name = name.replace('Verify_', '').replace('constructor', 'constr.')
			return f'Ver. ({name})'
		elif name == 'PublicKeyInfrastructure':
			return 'PKI'
		else:
			return name.replace('constructor', 'constr.')
	transaction_runs['name'] = transaction_runs['name'].apply(rename)

	return transaction_runs


def plot_cost_overview(p):
	transaction_runs = get_transaction_runs(p, True)

	# remove deploy
	transaction_runs = transaction_runs[transaction_runs['type'] != 'deploy']

	# extract relevant data
	grouped = transaction_runs.groupby(['contract'])
	data = grouped['gas'].apply(list)
	contracts = [k for k, _ in data.items()]
	gas = [gas for _, gas in data.items()]
	indices = [len(c)*[i] for i, c in enumerate(gas)]

	# PLOT FIGURE

	# prepare
	matplotlib.rcParams.update({'font.size': 18})
	fig, ax = plt.subplots(frameon=False, figsize=(8.0, 2.8))

	# set lines
	ax.yaxis.grid(True)
	ax.spines['left'].set_visible(False)
	ax.spines['top'].set_visible(False)
	ax.spines['bottom'].set_visible(False)
	ax.spines['right'].set_visible(False)

	# add dollar cost
	ax_dollar = add_cost_axis(ax, 16, 0.5)

	# set ticks
	min_gas, max_gas = min(flatten(gas)), max(flatten(gas))
	set_n_ticks(ax, ax_dollar, 2, min_gas, max_gas)

	# plot
	# bp = ax.boxplot(gas, sym='+')
	ax.plot(flatten(indices), flatten(gas), 'x', color='#FF9800')

	# set x axis labels
	ax.set_xticks(range(len(gas)))
	ax.set_xticklabels(contracts, rotation=40)

	# set axis range
	delta = 0.03
	ax.set_ylim((1-delta)*min(flatten(gas)), (1+delta)*max(flatten(gas)))

	# save result
	fig.tight_layout()
	pdf = os.path.join(script_dir, 'transaction_costs.pdf')
	plt.savefig(pdf)


def plot_transaction_cost(p, contract='MedStats'):
	transaction_runs = get_transaction_runs(p, False)
	costs = transaction_runs[transaction_runs['contract'] == contract]

	# PLOT
	matplotlib.rcParams.update({'font.size': 18})
	fig, ax = plt.subplots(frameon=False, figsize=(8.0, 2.8))

	# set lines
	ax.yaxis.grid(True)  # linewidth=0.5
	ax.spines['left'].set_visible(False)
	ax.spines['top'].set_visible(False)
	ax.spines['bottom'].set_visible(False)
	ax.spines['right'].set_visible(False)

	# add dollar cost
	ax_dollar = add_cost_axis(ax, 15, 0.5, n_digits=0)

	# set ticks
	max_gas = costs['gas'].max()
	set_n_ticks(ax, ax_dollar, 3, 0, max_gas)

	# plot
	all_indices = []
	next_start = 0
	plain_hatch = '//'
	priv_hatch = '\\\\'
	colors = {1: '#B3E5FC', 2: '#03A9F4', 3: '#FF9800'}
	hatches = {1: plain_hatch, 2: plain_hatch, 3: priv_hatch}
	legends = {1: 'global setup', 2: 'per contract', 3: 'per transaction'}
	for phase, group in costs.groupby('phase'):
		indices = np.linspace(next_start, next_start + len(group), len(group), endpoint=False)
		gas = group['gas'].tolist()
		ax.bar(indices, gas, color=colors[phase], hatch=hatches[phase], edgecolor="white", linewidth=0, label=legends[phase])

		next_start = indices[-1] + 1.5
		all_indices = np.concatenate((all_indices, indices), axis=None)

	# set labels
	ax.set_xticks(all_indices)
	ax.set_xticklabels(costs['name'].tolist(), rotation=45, ha='right', rotation_mode="anchor")

	# draw legend
	# legend = ax.legend(framealpha=1.0, handlelength=1.5)  # loc=(0.03, 0.65)
	# legend.get_frame().set_linewidth(0.0)

	# save result
	fig.tight_layout()
	pdf = os.path.join(script_dir, f'{contract}_costs.pdf')
	plt.savefig(pdf)


def main():
	p = get_data()
	# p.print_items()

	per_contract, per_contract_stats = get_per_contract_stats(p)
	# update description
	per_contract.set_index('contract', inplace=True)
	per_contract.at['MedStats', 'description'] += r' (\fig\ref{fig:overview})'

	print(per_contract)
	csv = os.path.join(script_dir, 'examples-overview.csv')
	per_contract.to_csv(csv)

	csv = os.path.join(script_dir, 'examples-overview-stats.csv')
	per_contract_stats.to_csv(csv, header=True)

	compile_time = get_compile_time_stats(p)
	csv = os.path.join(script_dir, 'examples-compile-time.csv')
	compile_time.to_csv(csv, header=True)

	transaction_time = get_transaction_time_stats(p)
	csv = os.path.join(script_dir, 'examples-transaction-time.csv')
	transaction_time.to_csv(csv, header=True)

	plot_cost_overview(p)
	plot_transaction_cost(p)


if __name__ == '__main__':
	main()
