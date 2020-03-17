#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import load_transaction_interface_for_benchmark
g = load_transaction_interface_for_benchmark(sys.argv[1])

# Scenario
insurance_addr, police_addr, client_addr = g.create_dummy_accounts(3)

insurance = g.deploy(police_addr, user=insurance_addr)
police = g.connect(insurance.address, user=police_addr)
client = g.connect(insurance.address, user=client_addr)

client.register()
client.insure_item(1000, 10)
client.insure_item(2000, 20)
client.retract_item(0)
insurance.accept_item(client_addr, 1)
police.set_stolen(client_addr, 1, True)
police.set_broken(client_addr, 1, False)
client.get_refund(1)
