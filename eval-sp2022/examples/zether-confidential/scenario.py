#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1], log_filename=sys.argv[2]) as g:
	sender_addr, receiver_addr = g.create_dummy_accounts(2)

	sender = g.deploy(user=sender_addr)
	receiver = g.connect(sender.address, user=receiver_addr)

	sender.fund(wei_amount=1000)
	sender.transfer(receiver_addr, 100)
	receiver.burn(40)
