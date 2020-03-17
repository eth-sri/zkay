#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	business_addr, customer1_addr, customer2_addr = g.create_dummy_accounts(3)

	business = g.deploy(user=business_addr)
	customer1 = g.connect(business.address, user=customer1_addr)
	customer2 = g.connect(business.address, user=customer2_addr)

	business.give_receipt(1234, 20)
	business.give_receipt(1235, 50)
	customer1.receive_receipt(1234, 20)
	customer2.receive_receipt(1235, 50)
	business.check(1234)
	business.check(1235)
