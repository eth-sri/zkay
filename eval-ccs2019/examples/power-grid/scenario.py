#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	master_addr, consumer_addr = g.create_dummy_accounts(2)

	master = g.deploy(user=master_addr)
	consumer = g.connect(master.address, user=consumer_addr)

	consumer.init()
	consumer.register_consumed(17)
	consumer.declare_total()

