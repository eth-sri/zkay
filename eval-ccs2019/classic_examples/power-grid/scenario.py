#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import load_transaction_interface_for_benchmark
g = load_transaction_interface_for_benchmark(sys.argv[1])

# Scenario
master_addr, consumer_addr = g.create_dummy_accounts(2)

master = g.deploy(user=master_addr)
consumer = g.connect(master.address, user=consumer_addr)

consumer.init()
consumer.register_consumed(17)
consumer.declare_total()

