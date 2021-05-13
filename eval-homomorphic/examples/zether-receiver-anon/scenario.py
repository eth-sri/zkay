#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	sender_addr, r1_addr, r2_addr, r3_addr = g.create_dummy_accounts(4)

	sender = g.deploy(user=sender_addr)
	r1 = g.connect(sender.address, user=r1_addr)
	r2 = g.connect(sender.address, user=r2_addr)

	sender.fund(wei_amount=1000)
	sender.transfer(r1_addr, r2_addr, 0, 100)
	r2.burn(40)
