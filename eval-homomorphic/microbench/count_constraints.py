#!/usr/bin/env python3
# usage ./count_constraints.py
import os

from zkay.jsnark_interface.jsnark_interface import compile_and_run_with_circuit_builder

here = os.path.realpath(os.path.dirname(__file__))
constraint_counter_java = os.path.join(here, "ConstraintCounter.java")

ret, err = compile_and_run_with_circuit_builder(here, "ConstraintCounter", constraint_counter_java, [])
if len(err) > 0:
    print("Error while running ConstraintCounter:")
    print(err)
print(ret)
