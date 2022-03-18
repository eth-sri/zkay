#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1], log_filename=sys.argv[2]) as g:
	owner_addr, other_addr = g.create_dummy_accounts(2)

	owner = g.deploy(user=owner_addr)
	other = g.connect(owner.address, user=other_addr)

	other.foo(4)
	owner.show_result()
