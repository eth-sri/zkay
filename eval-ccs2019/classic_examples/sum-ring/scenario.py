#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import load_transaction_interface_for_benchmark
g = load_transaction_interface_for_benchmark(sys.argv[1])

# Scenario
p1_addr, p2_addr, p3_addr = g.create_dummy_accounts(3)

p1 = g.deploy(12345, user=p1_addr)
p2 = g.connect(p1.address, user=p2_addr)
p3 = g.connect(p1.address, user=p3_addr)

p1.addVal(100, p2_addr)
p2.addVal(200, p3_addr)
p3.addVal(300, p1_addr)
p1.evaluateSum()
