#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	a_addr, b_addr, c_addr = g.create_dummy_accounts(3)

	a = g.deploy(user=a_addr)
	b = g.connect(a.address, user=b_addr)
	c = g.connect(a.address, user=c_addr)

	a.buy(wei_amount=100)
	b.buy(wei_amount=100)
	c.buy(wei_amount=100)
	a.pledge_inheritance(b_addr, 50)
	a.pledge_inheritance(c_addr, 20)

	a.sell(10)
	a.transfer(20, b_addr)

	a._test_advance_time()
	b.claim_inheritance(a_addr)
	c.claim_inheritance(a_addr)

	b.sell(170)
	c.sell(120)
