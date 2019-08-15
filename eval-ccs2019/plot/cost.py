from matplotlib import ticker
import numpy as np


# https://ethgasstation.info/index.php
# May 8, 2019
# "standard" gas price: 1 Gas = 3 Gwei
gas_to_gwei = 3
# 1 Gwei = 10^-9 ETH
gwei_to_eth = 1E-9
# 1 ETH = 170$
eth_to_usd = 170


def gas_to_dollar(gas):
	dollar = gas * gas_to_gwei * gwei_to_eth * eth_to_usd
	return dollar


def add_cost_axis(ax, fontsize, delta, n_digits=2):
	# add dollar axis
	ax_dollar = ax.twinx()

	# keep frame setting
	for p in ['top', 'right', 'bottom', 'left']:
		current = ax.spines[p].get_visible()
		ax_dollar.spines[p].set_visible(current)

	def convert_ax_to_dollar(ax_gas):
		y1, y2 = ax_gas.get_ylim()
		ax_dollar.set_ylim(gas_to_dollar(y1), gas_to_dollar(y2))
		ax_dollar.figure.canvas.draw()
	ax.callbacks.connect("ylim_changed", convert_ax_to_dollar)

	# set y axis labels
	def to_million(x, _):
		in_millions = x / 1000 / 1000
		return '$' + f'{in_millions:.{n_digits}f}' + ' \cdot 10^6$'
	million_formatter = ticker.FuncFormatter(to_million)
	ax.get_yaxis().set_major_formatter(million_formatter)

	# add axis labels
	ax.set_ylabel('Gas')
	ax_dollar.set_ylabel('US\$')
	details = f'1Gas={gas_to_gwei}Gwei,\n1ETH={eth_to_usd}\$'
	position = {
		'rotation': 90,
		'transform': ax.transAxes, 'horizontalalignment': 'center', 'verticalalignment': 'center'}
	ax_dollar.text(1.2, 0.5, details, fontsize=0.75*fontsize, **position)

	ax_dollar.text(1.2, 0.5 - delta, '(', fontsize=1.5*fontsize, **position)
	ax_dollar.text(1.2, 0.5 + delta, ')', fontsize=1.5*fontsize, **position)

	return ax_dollar


def set_n_ticks(ax, ax_dollar, n_ticks, min_gas, max_gas):
	ax.set_yticks(np.round(np.linspace(min_gas, max_gas, n_ticks), 2))
	ax_dollar.set_yticks(np.round(np.linspace(gas_to_dollar(min_gas), gas_to_dollar(max_gas), n_ticks), 2))
