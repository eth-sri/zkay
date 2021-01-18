from zkay.examples.scenario import ScenarioBuilder
admin, user, stock_a, stock_b = 'admin', 'user', 'stock_a', 'stock_b'
sb = ScenarioBuilder('IndexFund', 'code/IndexFund.zkay').set_users(admin, user, stock_a, stock_b)
sb.set_deployment_transaction(owner=admin)
sb.add_transaction('add_stocks_to_fund', [stock_a, 1, 10], user=admin)
sb.add_transaction('add_stocks_to_fund', [stock_b, 3, 5], user=admin)
sb.add_state_assertion('current_fund_price', expected_value=25)

sb.add_transaction('pay_into', amount=250, user=user)
sb.add_state_assertion('balance', user, user=user, expected_value=250, should_decrypt=True)
sb.add_balance_assertion(250)

sb.add_transaction('buy_shares', [10], user=user)
sb.add_state_assertion('balance', user, user=user, expected_value=0, should_decrypt=True)
sb.add_state_assertion('shares', user, user=user, expected_value=10, should_decrypt=True)
sb.add_state_assertion('total_shares', user=admin, expected_value=10, should_decrypt=True)

sb.add_transaction('pay_dividends', [user, 2], user=stock_a)
sb.add_state_assertion('balance', user, user=user, expected_value=20, should_decrypt=True)

sb.add_transaction('report_new_stock_price', [10], user=stock_b)
sb.add_state_assertion('current_fund_price', expected_value=40)

sb.add_transaction('sell_shares', [5], user=user)
sb.add_state_assertion('balance', user, user=user, expected_value=220, should_decrypt=True)
sb.add_state_assertion('shares', user, user=user, expected_value=5, should_decrypt=True)
sb.add_state_assertion('total_shares', user=admin, expected_value=5, should_decrypt=True)

SCENARIO = sb.build()
