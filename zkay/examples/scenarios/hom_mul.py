from zkay.examples.scenario import ScenarioBuilder
a, b = 'a', 'b'
sb = ScenarioBuilder('HomomorphicMultiplication', 'code/HomomorphicMultiplication.zkay').set_users(a, b)
sb.set_deployment_transaction(3, 2, owner=a)
sb.add_state_assertion('a', expected_value=3, should_decrypt=True)
sb.add_state_assertion('b', expected_value=2)
sb.add_transaction('f', user=b)
sb.add_state_assertion('productPosPos', expected_value=6, should_decrypt=True)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
