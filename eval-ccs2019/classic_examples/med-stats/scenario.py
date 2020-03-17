#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import load_transaction_interface_for_benchmark
g = load_transaction_interface_for_benchmark(sys.argv[1])

# Scenario
hospital_addr, patient1_addr, patient2_addr = g.create_dummy_accounts(3)

hospital = g.deploy(user=hospital_addr)
patient1 = g.connect(hospital.address, user=patient1_addr)
patient2 = g.connect(hospital.address, user=patient2_addr)

hospital.record(patient1_addr, True)
hospital.record(patient2_addr, False)
patient1.check(True)
patient2.check(False)
