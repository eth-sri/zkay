#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	state_addr, me_addr = g.create_dummy_accounts(2)

	state = g.deploy(user=state_addr)
	me = g.connect(state.address, user=me_addr)

	me.init()
	me.registerIncome(1)
	me.registerIncome(40000-1)
	me.checkEligibility()
