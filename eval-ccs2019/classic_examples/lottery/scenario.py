#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	master_addr, x_addr, y_addr = g.create_dummy_accounts(3)

	master = g.deploy(1234, user=master_addr)
	x = g.connect(master.address, user=x_addr)
	y = g.connect(master.address, user=y_addr)

	x.bet(1234)
	y.bet(1235)
	master.publish_secret()
	x.claim_winner()
