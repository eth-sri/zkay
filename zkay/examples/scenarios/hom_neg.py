from zkay.examples.scenario import ScenarioBuilder
a, b = 'a', 'b'
sb = ScenarioBuilder('HomomorphicNegation', 'code/HomomorphicNegation.zkay').set_users(a, b)
sb.set_deployment_transaction(3, owner=a)
sb.add_state_assertion('x', expected_value=3, should_decrypt=True)
sb.add_transaction('f', user=b)
sb.add_state_assertion('x', expected_value=-3, should_decrypt=True)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
