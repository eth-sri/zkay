#!/usr/bin/env python3
# usage ./extract_results.py (after running benchmark.py)

import re
import os
file_dir = os.path.realpath(os.path.dirname(__file__))
cwd = os.path.join(file_dir, 'examples')

frame_names = ['compilation time', 'compilation average memory', 'compilation peak memory', 'scenario runtime', 'scenario average gas', 'scenario average memory', 'scenario peak memory']


def get_data(outdir):
    os.chdir(outdir)
    full_pat = re.compile(r'{"key": "compileFull", "value": (\d*\.\d*),')
    with open('compile_data.log') as f:
        d = f.read()
    c_time = float(full_pat.search(d).group(1))

    with open('mprof_compile.dat') as f:
        d = f.read().splitlines()[1:]
    mem = [float(l.split(' ')[1]) for l in d]
    c_avg_mem = sum(mem) / len(mem)
    c_peak_mem = max(mem)

    full_pat = re.compile(r'{"key": "all_transactions", "value": (\d*\.\d*), "context":')
    with open('log_data.log') as f:
        d = f.read()
    t_time = float(full_pat.search(d).group(1))
    cost_pat = re.compile(r'"key": "gas", "value": (\d+),.*?"context": (?!(?:(?:\[\["transaction", "(?:constructor_0|announcePk|deploy_pki|deploy_verify_libs)"\]\])|\[\]))')
    tot_cost = 0
    count = 0
    for m in cost_pat.finditer(d):
        tot_cost += int(m.group(1))
        count += 1
    t_avg_gas = tot_cost / count

    with open('mprof_run.dat') as f:
        d = f.read().splitlines()[1:]
    mem = [float(l.split(' ')[1]) for l in d]
    t_avg_mem = sum(mem) / len(mem)
    t_peak_mem = max(mem)

    os.chdir(cwd)

    return c_time, c_avg_mem, c_peak_mem, t_time, t_avg_gas, t_avg_mem, t_peak_mem


scenarios = [d for d in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, d))]
data = [[dict({'scenario': scenario, 'val': -1}) for scenario in scenarios] for _ in range(len(frame_names))]
for dir_idx, dirname in enumerate(scenarios):
    try:
        res = get_data(os.path.join(cwd, dirname, 'out'))
        for idx, val in enumerate(res):
            data[idx][dir_idx]['scenario'] = dirname
            data[idx][dir_idx]['val'] = val
    except:
        pass

import csv
for idx, frame in enumerate(frame_names):
    with open(os.path.join(file_dir, f'{frame}.csv'), 'w') as f:
        w = csv.DictWriter(f, data[idx][0].keys())
        w.writeheader()
        w.writerows(data[idx])
