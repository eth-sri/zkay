#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	hospital_addr, patient1_addr, patient2_addr = g.create_dummy_accounts(3)

	hospital = g.deploy(user=hospital_addr)
	patient1 = g.connect(hospital.address, user=patient1_addr)
	patient2 = g.connect(hospital.address, user=patient2_addr)

	hospital.record(patient1_addr, True)
	hospital.record(patient2_addr, False)
	patient1.check(True)
	patient2.check(False)
