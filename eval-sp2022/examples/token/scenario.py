#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1], log_filename=sys.argv[2]) as g:
	sender_addr, receiver_addr = g.create_dummy_accounts(2)

	sender = g.deploy(user=sender_addr)
	receiver = g.connect(sender.address, user=receiver_addr)

	sender.buy(wei_amount=1000)
	sender.transfer(100, receiver_addr)
	receiver.sell(40)
