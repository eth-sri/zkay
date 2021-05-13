#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	issuer_addr, owner_addr = g.create_dummy_accounts(2)

	issuer = g.deploy(owner_addr, user=issuer_addr)
	owner = g.connect(issuer.address, user=owner_addr)

	issuer.updateBalance(59, wei_amount=100)
	issuer.updateBalance(48, wei_amount=100)
	owner.redeemBonus()
