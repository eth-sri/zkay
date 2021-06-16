#!/usr/bin/env python3
# usage ./extract_metadata.py

import re
import os
from operator import itemgetter

from zkay.utils.helpers import lines_of_code

file_dir = os.path.realpath(os.path.dirname(__file__))
cwd = os.path.join(file_dir, 'examples')


scenarios = [d for d in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, d))]
all_metadata = []
for name in scenarios:
    contract_file_name = os.path.join(cwd, name, name + ".zkay")
    if os.path.exists(contract_file_name):
        metadata = {}
        with open(contract_file_name, "r") as f:
            code = f.read()
            metadata['LOC'] = lines_of_code(code)
            lines = code.split("\n")
            for line in lines:
                obj = re.match(r"^// META-([A-Z]+)( (.*))?$", line)
                if obj is not None:
                    g = obj.groups()
                    metadata[g[0]] = g[2]
        if "NAME" in metadata:
            all_metadata.append(metadata)

print("xxno,xxcontract,xxdescription,xxloc,xxadd,xxmult,xxmixed")
for idx, data in enumerate(sorted(all_metadata, key=itemgetter("NAME"))):
    if "NAME" not in data:
        continue
    x_add = "\\xyes" if "ADD" in data else "\\xno"
    x_mult = "\\xyes" if "MULT" in data else "\\xno"
    x_mixed = "\\xyes" if "MIXED" in data else "\\xno"
    print(f"{idx+1},{data['NAME']},{data['DESC']},{data['LOC']},{x_add},{x_mult},{x_mixed}")
