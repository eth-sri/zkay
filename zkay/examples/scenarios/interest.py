from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

bank, a, b = 'bank', 'a', 'b'
sb = ScenarioBuilder('Interest', 'code/Interest.zkay').set_users(bank, a, b)
sb.set_deployment_transaction(owner=bank)

sb.add_transaction('register', user=a)
sb.add_transaction('buy', amount=125, user=a)
sb.add_transaction('register', user=b)
sb.add_transaction('buy', amount=225, user=b)
sb.add_balance_assertion(350)
sb.add_state_assertion('checkings', a, user=a, expected_value=125, should_decrypt=True)
sb.add_state_assertion('checkings', b, user=b, expected_value=225, should_decrypt=True)

sb.add_transaction('send_tokens', [25, b], user=a)
sb.add_state_assertion('checkings', a, user=a, expected_value=100, should_decrypt=True)
sb.add_state_assertion('checkings', b, user=b, expected_value=250, should_decrypt=True)

sb.add_transaction('invest', [100], user=a)
sb.add_transaction('invest', [300], user=b, expected_exception=RequireException)
sb.add_transaction('invest', [200], user=b)
sb.add_transaction('invest', [100], user=b, expected_exception=RequireException)
sb.add_state_assertion('checkings', a, user=a, expected_value=0, should_decrypt=True)
sb.add_state_assertion('checkings', b, user=b, expected_value=50, should_decrypt=True)
sb.add_state_assertion('investments', a, user=a, expected_value=100, should_decrypt=True)
sb.add_state_assertion('investments', b, user=b, expected_value=200, should_decrypt=True)
sb.add_state_assertion('bank_total_investments', user=bank, expected_value=300, should_decrypt=True)

sb.add_transaction('pay_out_investment', user=a, expected_exception=RequireException)
sb.add_transaction('_test_advance_time', user=bank)
sb.add_transaction('pay_out_investment', user=a)
sb.add_transaction('pay_out_investment', user=b)

sb.add_state_assertion('checkings', a, user=a, expected_value=105, should_decrypt=True)
sb.add_state_assertion('checkings', b, user=b, expected_value=260, should_decrypt=True)
sb.add_state_assertion('investments', a, user=a, expected_value=0, should_decrypt=True)
sb.add_state_assertion('investments', b, user=b, expected_value=0, should_decrypt=True)
sb.add_state_assertion('bank_total_investments', user=bank, expected_value=0, should_decrypt=True)

sb.add_transaction('pay_out_investment', user=a, expected_exception=RequireException)

SCENARIO = sb.build()
