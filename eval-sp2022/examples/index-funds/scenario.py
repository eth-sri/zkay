#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1], log_filename=sys.argv[2]) as g:
	admin_addr, user_addr, stock_1_addr, stock_2_addr = g.create_dummy_accounts(4)

	admin = g.deploy(user=admin_addr)
	user = g.connect(admin.address, user=user_addr)
	stock_1 = g.connect(admin.address, user=stock_1_addr)
	stock_2 = g.connect(admin.address, user=stock_2_addr)

	admin.add_stocks_to_funds(stock_1_addr, 1, 10)
	admin.add_stocks_to_funds(stock_2_addr, 3, 5)

	user.pay_into(wei_amount=250)
	user.buy_shares(10)

	stock_2.report_new_stock_price(2)
	user.sell_shares(5)
	user.pay_out(50)
