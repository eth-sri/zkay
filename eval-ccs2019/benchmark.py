#!/usr/bin/env python3
# usage ./benchmark.py [example_dir]
# (example_dir contains subdirectories with example sol/zkay and scenario files)

# requires installed memory-profiler and zkay packages

import os
import datetime
import sys
import shutil
clean=False
file_dir = os.path.realpath(os.path.dirname(__file__))
base_dir = os.path.join(file_dir, 'examples') if len(sys.argv) < 2 else os.path.realpath(sys.argv[1])
backends = ['dummy', 'ecdh-chaskey', 'ecdh-aes'] #, 'rsa-pkcs1.5', 'rsa-oaep'] # rsa consumes >100 GB hdd space

for backend in backends:
    for dirname in os.listdir(base_dir):
        p = os.path.join(base_dir, dirname)
        if os.path.isdir(p):
            file = None
            for filename in os.listdir(p):
                if filename.endswith(('.sol', '.zkay')):
                    file = os.path.join(p, filename)
                    break
            if file is not None:
                out_dir = os.path.join(p, f'out_{backend}')
                if clean and os.path.exists(out_dir):
                    shutil.rmtree(out_dir)
                os.makedirs(out_dir, exist_ok=True)
                print(f'compiling {file}, at {datetime.datetime.utcnow()}')
                os.system(f"mprof run --include-children --nopython -o '{out_dir}/mprof_compile.dat' zkay compile '{file}' --verbosity 0 --crypto-backend {backend} --opt-hash-threshold 0 -o '{out_dir}' --log --log-dir '{out_dir}'")

                scenario_file = os.path.join(p, 'scenario.py')
                if os.path.exists(scenario_file):
                    print(f'running {scenario_file}, at {datetime.datetime.utcnow()}')
                    os.system(f"mprof run --include-children --nopython -o '{out_dir}/mprof_run.dat' python '{scenario_file}' '{out_dir}'")
