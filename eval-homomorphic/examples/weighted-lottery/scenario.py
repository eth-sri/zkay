#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	lottery_addr, b1_addr, b2_addr = g.create_dummy_accounts(3)

	lottery = g.deploy(user=lottery_addr)
	b1 = g.connect(lottery.address, user=b1_addr)
	b2 = g.connect(lottery.address, user=b2_addr)

	b1.buy(wei_amount=1000)
	b2.buy(wei_amount=1000)
	lottery.start(193775903028374)
	b1.bet(193775903028370, 100)
	b2.bet(20483, 20)

	lottery._test_advance_time()
	lottery.add_winner(b1_addr)
	lottery.publish()

	lottery._test_advance_time()
	b1.win()
	b1.sell(1020)
