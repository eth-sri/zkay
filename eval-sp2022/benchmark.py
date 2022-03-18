#!/usr/bin/env python3
# usage ./benchmark.py [example_dir]
# (example_dir contains subdirectories with example sol/zkay and scenario files)

# requires installed memory-profiler and zkay packages

import os
import datetime
import sys
import shutil
clean = True
file_dir = os.path.realpath(os.path.dirname(__file__))
base_dir = os.path.join(file_dir, 'examples') if len(sys.argv) < 2 else os.path.realpath(sys.argv[1])

main_crypto_backend = 'ecdh-chaskey'
homomorphic_crypto_backend = 'elgamal'


def run_with_mprof(out_file, cmd):
    tmp_file = f"{out_file}_tmp"
    try:
        os.system(f"mprof run --include-children --nopython -o '{tmp_file}' {cmd}")
        with open(tmp_file, 'r') as f:
            data = f.read().splitlines(True)
        with open(out_file, 'w') as f:
            f.writelines(data[1:])  # drop first line as it contains privacy-sensitive path information
    finally:
        os.remove(tmp_file)


for dirname in os.listdir(base_dir):
    p = os.path.join(base_dir, dirname)
    if os.path.isdir(p):
        file = None
        for filename in os.listdir(p):
            if filename.endswith(('.sol', '.zkay')):
                file = os.path.join(p, filename)
                break
        if file is not None:
            out_dir = os.path.join(p, 'out')
            if clean and os.path.exists(out_dir):
                shutil.rmtree(out_dir)
            os.makedirs(out_dir, exist_ok=True)

            compile_args = f"--verbosity 0 --main-crypto-backend {main_crypto_backend} --addhom-crypto-backend {homomorphic_crypto_backend} --opt-hash-threshold 0 -o '{out_dir}'"

            print(f'compiling {file}, at {datetime.datetime.utcnow()}')
            run_with_mprof(f"{out_dir}/mprof_compile.dat", f"zkay compile '{file}' {compile_args} --log --log-dir '{out_dir}'")

            scenario_file = os.path.join(p, 'scenario.py')
            if os.path.exists(scenario_file):
                print(f'running {scenario_file}, at {datetime.datetime.utcnow()}')
                run_with_mprof(f"{out_dir}/mprof_run.dat", f"python '{scenario_file}' '{out_dir}' log")

            print(f'compiling {file} with disabled verification, at {datetime.datetime.utcnow()}')
            os.system(f"zkay compile '{file}' {compile_args} --disable-verification")

            if os.path.exists(scenario_file):
                print(f'running {scenario_file} with disabled verification, at {datetime.datetime.utcnow()}')
                os.system(f"python '{scenario_file}' '{out_dir}' log_no_verification")
