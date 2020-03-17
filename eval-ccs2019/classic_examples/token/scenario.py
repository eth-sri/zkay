#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import load_transaction_interface_for_benchmark
g = load_transaction_interface_for_benchmark(sys.argv[1])

# Scenario
sender_addr, receiver_addr = g.create_dummy_accounts(2)

sender = g.deploy(user=sender_addr)
receiver = g.connect(sender.address, user=receiver_addr)

sender.register()
receiver.register()
sender.buy(1000)
sender.send_tokens(100, receiver_addr)
receiver.receive_tokens(sender_addr)

