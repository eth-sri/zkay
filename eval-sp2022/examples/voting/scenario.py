#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1], log_filename=sys.argv[2]) as g:
	a_addr, b_addr, c_addr, owner_addr = g.create_dummy_accounts(4)

	owner = g.deploy(user=owner_addr)
	a = g.connect(owner.address, user=a_addr)
	b = g.connect(owner.address, user=b_addr)
	c = g.connect(owner.address, user=c_addr)

	a.vote(0)
	b.vote(1)
	c.vote(1)
	owner.declareWinner()
