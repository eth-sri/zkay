#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1], log_filename=sys.argv[2]) as g:
	receiver_addr, sender_addr = g.create_dummy_accounts(2)

	receiver = g.deploy(user=receiver_addr)
	sender = g.connect(receiver.address, user=sender_addr)

	receiver.prepare(0, 1)
	sender.send(24, 59)

	receiver.prepare(1, 0)
	sender.send(42, 18)
