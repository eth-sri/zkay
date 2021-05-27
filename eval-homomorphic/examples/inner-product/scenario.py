#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	owner_addr, other_addr = g.create_dummy_accounts(2)

	owner = g.deploy(user=owner_addr)
	other = g.connect(owner.address, user=other_addr)

	owner.set_entry(0, 2)
	owner.set_entry(1, 3)
	owner.set_entry(2, 9)
	other.compute(6, 3, 0)
