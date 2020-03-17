#!/usr/bin/env python3
# usage ./benchmark.py (compile|run) example_dir
# (example_dir contains subdirectories with example sol/zkay files)
import os
import datetime
import sys
import shutil
clean=False
base_dir = sys.argv[2]
backends = ['dummy', 'rsa-pkcs1.5', 'rsa-oaep', 'ecdh-aes', 'ecdh-chaskey']

if sys.argv[1] == 'compile':
    for dirname in os.listdir(base_dir):
        p = os.path.join(base_dir, dirname)
        if os.path.isdir(p):
            file = None
            for filename in os.listdir(p):
                if filename.endswith(('.sol', '.zkay')):
                    file = os.path.join(p, filename)
                    break
            if file is not None:
                for backend in backends:
                    out_dir = os.path.join(p, f'out_{backend}')
                    if clean and os.path.exists(out_dir):
                        shutil.rmtree(out_dir)
                    os.makedirs(out_dir, exist_ok=True)
                    print(f'compiling {file}, at {datetime.datetime.utcnow()}')
                    os.system(f"mprof run --include-children --nopython -o '{out_dir}/mprof_compile.dat' zkay compile '{file}' --verbosity 0 --crypto-backend {backend} --opt-hash-threshold 0 -o '{out_dir}' --log --log-dir '{out_dir}'")
else:
    assert sys.argv[1] == 'run'
    for dirname in os.listdir(base_dir):
        p = os.path.join(base_dir, dirname)
        if os.path.isdir(p):
            file = os.path.join(p, 'scenario.py')
            if os.path.exists(file):
                for backend in backends:
                    out_dir = os.path.join(p, f'out_{backend}')
                    print(f'running {file}, at {datetime.datetime.utcnow()}')
                    os.system(f"mprof run --include-children --nopython -o '{out_dir}/mprof_run.dat' python '{file}' '{out_dir}'")
