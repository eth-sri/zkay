#!/usr/bin/env python3
# usage ./extract_metadata.py

import re
import os
file_dir = os.path.realpath(os.path.dirname(__file__))
cwd = os.path.join(file_dir, 'examples')


scenarios = [d for d in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, d))]
metadata = {}
for name in scenarios:
    contract_file_name = os.path.join(cwd, name, name + ".zkay")
    if os.path.exists(contract_file_name):
        metadata[name] = {}
        loc = 0
        with open(contract_file_name, "r") as f:
            for line in f:
                line = line[:-1]    # remove linebreak
                if line != "":
                    loc += 1
                obj = re.match(r"^// META-([A-Z]+)( (.*))?$", line)
                if obj is not None:
                    g = obj.groups()
                    metadata[name][g[0]] = g[2]
        metadata[name]['LOC'] = loc     # for the moment simply counts non-emtpy lines

print("xxcontract,xxdescription,xxloc,xxadd,xxmult,xxmixed")
for _, data in metadata.items():
    if "NAME" not in data:
        continue
    x_add = "\\xyes" if "ADD" in data else "\\xno"
    x_mult = "\\xyes" if "MULT" in data else "\\xno"
    x_mixed = "\\xyes" if "MIXED" in data else "\\xno"
    print(f"{data['NAME']},{data['DESC']},{data['LOC']},{x_add},{x_mult},{x_mixed}")
