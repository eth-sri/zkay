#!/usr/bin/env python3
# usage ./generate_plots.py (after running benchmark.py)

import re
import os
import pandas as pd
import json
import matplotlib.pyplot as plt
import sri_plot_helper as sph
import math

file_dir = os.path.realpath(os.path.dirname(__file__))
cwd = os.path.join(file_dir, 'examples')

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

EXAMPLE_X_GAP = 3
TX_X_GAP = 1.2
FONT_SIZE = 9
FONT_SIZE_LEGEND = 8

COLOR_T_DECRYPT = "#12356D"
COLOR_T_PROOF_GEN = "#547BB9"
COLOR_T_REST = "#B5C4DD"
COLOR_MEM = "#F5D250"
COLOR_MEM_TEXT = "#B2972E"
COLOR_GAS_VERIFY = "#792222"
COLOR_GAS_REST = "#D26464"
COLOR_GAS_DEPLOY = "#EDBBBB"


def next_bar_stack(ax, x_pos, data, offset, label, color):
    b = ax.bar(x_pos, width=1, height=data, bottom=offset, color=color)
    b.set_label(label)
    return offset + data


def match_key(obj, key):
    if "key" in obj:
        return obj["key"] == key
    return False


def get_callname(obj):
    ctx = obj["context"]
    if len(ctx) == 3 and ctx[2].startswith("zk__"):
            return ctx[2]
    return ctx[0]


def try_get_else_zero(data, key):
    if key in data:
        return data[key]
    return 0


def get_mem(mprof_fname: str):
    with open(mprof_fname) as f:
        d = f.read().splitlines()
    mem = [float(l.split(' ')[1]) for l in d]
    avg_mem = sum(mem) / len(mem)
    peak_mem = max(mem)
    return avg_mem / 1024, peak_mem / 1024   # in GiB


def is_ignored(callname):
    return callname in ["deploy_pki", "announcePk"] or callname.startswith("_test")


def is_deployment(callname):
    return callname == "constructor_0" or callname.startswith("zk__")


def process_gas(obj, data):
    callname = get_callname(obj)
    data[callname] = obj["value"]


def get_for_idx(df, idx, tx_idx, column_name):
    return df[(df.idx == idx) & (df.tx_idx == tx_idx)][column_name].item()


def get_data(outdir, example_idx, name, mem_data, compile_data, transact_data, gas_data, all_decrypt_times):
    os.chdir(outdir)
    c_avg_mem, c_peak_mem = get_mem('mprof_compile.dat')
    t_avg_mem, t_peak_mem = get_mem('mprof_run.dat')
    mem_data.append({'name': name, 'idx': example_idx, 'mem_c_avg': c_avg_mem, 'mem_c_peak': c_peak_mem, 'mem_t_avg': t_avg_mem, 'mem_t_peak': t_peak_mem})

    with open('compile_data.log', 'r') as f:
        for line in f:
            obj = json.loads(line)
            if match_key(obj, "time_compileFull"):
                c_time_full = obj["value"]
            elif match_key(obj, "time_key_generation"):
                c_time_keygen = obj["value"]
            elif match_key(obj, "time_circuit_compilation"):
                c_time_circuit = obj["value"]
    compile_data.append({'name': name, 'idx': example_idx, 'time_c_full': c_time_full, 'time_c_keygen': c_time_keygen, 'time_c_circuit': c_time_circuit, 'frac_time_c_keygen': c_time_keygen / c_time_full})

    time_tx_data = {}
    time_proof_data = {}
    time_decrypt_data = {}
    gas_tx_data = {}
    idx_for_callname = {}
    with open('log_data.log', 'r') as f:
        for line in f:
            obj = json.loads(line)
            if match_key(obj, "gas"):
                callname = get_callname(obj)
                if not is_ignored(callname):
                    idx_for_callname[callname] = len(idx_for_callname)
                    process_gas(obj, gas_tx_data)
            if match_key(obj, "time_transaction_full"):
                callname = get_callname(obj)
                if not is_ignored(callname):
                    time_tx_data[callname] = obj["value"]
            elif match_key(obj, "time_generate_proof"):
                time_proof_data[get_callname(obj)] = obj["value"]
            elif match_key(obj, "time_elgamal_decrypt"):
                callname = get_callname(obj)
                if callname not in time_decrypt_data:
                    time_decrypt_data[callname] = 0
                all_decrypt_times.append(obj["value"])
                time_decrypt_data[callname] += obj["value"]

    gas_no_verif_tx_data = {}
    with open('log_no_verification_data.log', 'r') as f:
        for line in f:
            obj = json.loads(line)
            if match_key(obj, "gas"):
                if not is_ignored(get_callname(obj)):
                    process_gas(obj, gas_no_verif_tx_data)

    for callname in time_tx_data:
        transact_data.append({'name': name, 'idx': example_idx, 'tx_idx': idx_for_callname[callname], 'tx_call': callname, 'is_deployment': is_deployment(callname),
                              'time_tx_full': time_tx_data[callname], 'time_tx_proof': try_get_else_zero(time_proof_data, callname),
                              'time_tx_decrypt': try_get_else_zero(time_decrypt_data, callname)})

    for callname in gas_tx_data:
        gas_all = gas_tx_data[callname]
        gas_rest = gas_no_verif_tx_data[callname]
        gas_verify = gas_all - gas_rest
        gas_data.append({'name': name, 'idx': example_idx, 'tx_idx': idx_for_callname[callname], 'tx_call': callname, 'is_deployment': is_deployment(callname),
                         'gas': gas_all, 'gas_verify': gas_verify, 'gas_rest': gas_rest})

    os.chdir(cwd)
    return len(idx_for_callname)


# load all the data from logs
mem_data = []
compile_data = []
transact_data = []
gas_data = []
all_decrypt_times = []
nof_tx = {}
example_names = [d for d in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, d))]
example_names.sort()
for example_idx, example_name in enumerate(example_names):
    out_dir = os.path.join(cwd, example_name, 'out')
    if os.path.exists(out_dir):
        nof_tx[example_idx] = get_data(out_dir, example_idx, example_name, mem_data, compile_data, transact_data, gas_data, all_decrypt_times)

# create data frames
df_mem = pd.DataFrame(mem_data)
df_compile = pd.DataFrame(compile_data)
df_transact = pd.DataFrame(transact_data)
df_gas = pd.DataFrame(gas_data)

df_t = df_mem[df_mem.mem_c_peak == df_mem.mem_c_peak.max()]
print("% Maximum compilation peak memory")
print("\\newcommand{\\evalcompmaxmemname}{" + df_t['name'].item() + "}")
print("\\newcommand{\\evalcompmaxmem}{$%.2f$}" % df_t['mem_c_peak'].item())
print()

df_t = df_compile[df_compile.time_c_full == df_compile.time_c_full.max()]
print("% Maximum compilation time")
print("\\newcommand{\\evalcompmaxtimename}{" + df_t['name'].item() + "}")
print("\\newcommand{\\evalcompmaxtime}{$%.1f$}" % df_t['time_c_full'].item())
print()

df_t = df_compile[df_compile.time_c_full == df_compile.time_c_full.min()]
print("% Minimum compilation time")
print("\\newcommand{\\evalcompmintimename}{" + df_t['name'].item() + "}")
print("\\newcommand{\\evalcompmintime}{$%.1f$}" % df_t['time_c_full'].item())
print()

print("% Average compilation time")
print("\\newcommand{\\evalcompavgtime}{$%.1f$}" % df_compile.time_c_full.mean())
print()

print("% Average key generation time fraction:")
print("\\newcommand{\\evalcompkeygenavgpercent}{$%.0f$}" % (df_compile.frac_time_c_keygen.mean() * 100))
print()

df_t = df_transact[df_transact.time_tx_full == df_transact.time_tx_full.max()]
print("% Maximum transaction generation time")
print("\\newcommand{\\evaltxmaxtimename}{" + df_t['name'].item() + "}")
print("\\newcommand{\\evaltxmaxtime}{$%.1f$}" % df_t['time_tx_full'].item())
print()

frac_proof = (df_transact.time_tx_proof.sum() / df_transact.time_tx_full.sum()) * 100
print("% Transaction generation time: proof fraction")
print("\\newcommand{\\evaltxfracprooftime}{$%.0f$}" % frac_proof)
print()

print("% Transaction generation time: decrypt fraction")
frac_decrypt = (df_transact.time_tx_decrypt.sum() / df_transact.time_tx_full.sum()) * 100
print("\\newcommand{\\evaltxfracdecrypttime}{$%.0f$}" % frac_decrypt)
print()

print("% Maximum single decryption time")
print("\\newcommand{\\evalmaxsingledecryptiontime}{$%.0f$~s}" % math.ceil(max(all_decrypt_times)))
print()

df_t = df_mem[df_mem.mem_t_peak == df_mem.mem_t_peak.max()]
print("% Maximum transaction generation peak memory")
print("\\newcommand{\\evaltxmaxmemname}{" + df_t['name'].item() + "}")
print("\\newcommand{\\evaltxmaxmem}{$%.1f$}" % df_t['mem_t_peak'].item())
print()

df_t = df_gas.sort_values(by='gas', ascending=False)
print("% Maximum transaction gas (incl. deployment)")
print("\\newcommand{\\evaltxmaxgasdeployname}{" + df_t.iloc[0, :]["name"] + "}")
print("\\newcommand{\\evaltxmaxgasdeploy}{$%.2f$~M}" % (df_t.iloc[0, :]["gas"] / 1.0e6))
print("\\newcommand{\\evaltxmaxgasdeploynamesecond}{" + df_t.iloc[1, :]["name"] + "}")
print("\\newcommand{\\evaltxmaxgasdeploysecond}{$%.2f$~M}" % (df_t.iloc[1, :]["gas"] / 1.0e6))
print()

df_t = df_gas[df_gas.is_deployment == False]
df_t = df_t[df_t.gas == df_t.gas.max()]
print("% Maximum transaction gas (excl. deployment)")
print("\\newcommand{\\evaltxmaxgasname}{" + df_t['name'].item() + "}")
print("\\newcommand{\\evaltxmaxgas}{$%.2f$~k}" % (df_t['gas'].item() / 1.0e3))
print()

df_t = df_gas[df_gas.is_deployment == False]
print("% Average transaction gas (excl. deployment)")
print("\\newcommand{\\evaltxavggas}{$%.0f$~k}" % (df_t.gas.mean() / 1.0e3))
print()

df_t = df_gas.query('name == "zether-confidential" & tx_call == "transfer_0"')
print("% Gas for zether-confidential, transfer")
print("\\newcommand{\\evaltxgastransfer}{$%.2f$~k}" % (df_t['gas'].item() / 1.0e3))
print()


# compute remainder tx time
df_transact = df_transact.assign(time_tx_rest=lambda df: df.time_tx_full - df.time_tx_proof - df.time_tx_decrypt)

# prepare x offsets for plots
x_pos_for = {}
x_pos_start = {}
x_pos_end = {}
x_pos_center = {}
cur_x_pos = 0
for example_idx in range(0, len(example_names)):
    x_pos_for[example_idx] = {}
    x_pos_start[example_idx] = cur_x_pos
    for tx_idx in range(0, nof_tx[example_idx]):
        x_pos_for[example_idx][tx_idx] = cur_x_pos
        cur_x_pos += TX_X_GAP
    x_pos_end[example_idx] = cur_x_pos - TX_X_GAP
    x_pos_center[example_idx] = x_pos_start[example_idx] + (x_pos_end[example_idx] - x_pos_start[example_idx]) / 2
    cur_x_pos += EXAMPLE_X_GAP  # gap between examples


def add_x_pos(df):
    df['plot_x_pos'] = [x_pos_for[x][y] for x, y in zip(df['idx'], df['tx_idx'])]


add_x_pos(df_transact)
add_x_pos(df_gas)

# setup plots
sph.configure_plots("IEEE", FONT_SIZE)

fig, axes = sph.subplots(2, 1, figsize=(19, 7.5), gridspec_kw={'height_ratios': [3, 2]})

# transaction plot
offset = next_bar_stack(axes[0], df_transact['plot_x_pos'], df_transact['time_tx_proof'], 0, "proof gen.", color=COLOR_T_PROOF_GEN)
offset = next_bar_stack(axes[0], df_transact['plot_x_pos'], df_transact['time_tx_decrypt'], offset, "decryption", color=COLOR_T_DECRYPT)
offset = next_bar_stack(axes[0], df_transact['plot_x_pos'], df_transact['time_tx_rest'], offset, "other", color=COLOR_T_REST)
axes[0].tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)     # remove x ticks
for example_idx, _ in enumerate(example_names):
    axes[0].text(x_pos_center[example_idx], -5, "\\textbf{" + str(example_idx + 1) + "}", ha='center', va='center')
axes[0].set_ylabel("time [s]")
axes[0].yaxis.set_major_locator(plt.MultipleLocator(10))   # set spacing of y-grid

# memory plot
ax_mem = axes[0].twinx()
ax_mem.spines['top'].set_visible(False)
ax_mem.spines['right'].set_visible(False)
ax_mem.spines['bottom'].set_visible(False)
ax_mem.spines['left'].set_visible(False)
ax_mem.set_ylabel("peak memory [GiB]")
ax_mem.yaxis.label.set_color(COLOR_MEM_TEXT)
ax_mem.tick_params(axis='y', colors=COLOR_MEM_TEXT)
ax_mem.set_ylim([0, 5])
for example_idx, _ in enumerate(example_names):
    ax_mem.hlines(df_mem[df_mem['idx'] == example_idx]['mem_t_peak'].values, x_pos_start[example_idx] - 0.5, x_pos_end[example_idx] + 0.5, colors=COLOR_MEM)

# combine legends
proxy_line = plt.Line2D([], [], color=COLOR_MEM, label="peak mem.")
h, _ = axes[0].get_legend_handles_labels()
h = [h[2], h[1], h[0], proxy_line]      # re-order legend
axes[0].legend(handles=h, bbox_to_anchor=(1.06, 1.05), fontsize=FONT_SIZE_LEGEND)

# gas plot
df_gas_deploy = df_gas[df_gas.is_deployment == True]
next_bar_stack(axes[1], df_gas_deploy['plot_x_pos'], df_gas_deploy['gas'], 0, "deployment", color=COLOR_GAS_DEPLOY)

df_gas_reg = df_gas[df_gas.is_deployment == False]
offset = next_bar_stack(axes[1], df_gas_reg['plot_x_pos'], df_gas_reg['gas_verify'], 0, "proof verif.", color=COLOR_GAS_VERIFY)
offset = next_bar_stack(axes[1], df_gas_reg['plot_x_pos'], df_gas_reg['gas_rest'], offset, "other", color=COLOR_GAS_REST)

axes[1].tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)     # remove x ticks
for example_idx, _ in enumerate(example_names):
    axes[1].text(x_pos_center[example_idx], -120000, "\\textbf{" + str(example_idx + 1) + "}", ha='center', va='center')
h, _ = axes[1].get_legend_handles_labels()
axes[1].legend(handles=[h[0], h[2], h[1]], bbox_to_anchor=(1.06, 1.05), fontsize=FONT_SIZE_LEGEND)
axes[1].set_ylabel("costs [gas]")
axes[1].yaxis.set_major_locator(plt.MultipleLocator(0.25e6))   # set spacing of y-grid

# configure clipping, numbers for outliers
y_clipping_limit = 1e6
axes[1].set_ylim([0, y_clipping_limit])
for i in range(0, len(x_pos_for)):
    for j in range(0, len(x_pos_for[i])):
        y_val = get_for_idx(df_gas, i, j, "gas")
        if y_val >= y_clipping_limit:
            axes[1].text(x_pos_for[i][j], y_clipping_limit + 0.05e6, "%.2f" % (y_val / 1e6),
                         ha='center', fontsize=8, color=COLOR_GAS_DEPLOY)

# fix layout
fig.tight_layout()

# save output
output_file = os.path.join(file_dir, 'plot.pdf')
sph.savefig(output_file)
