from zkay.examples.scenario import ScenarioBuilder
a, b = 'a', 'b'
sb = ScenarioBuilder('HomomorphicAddition', 'code/HomomorphicAddition.zkay').set_users(a, b)
sb.set_deployment_transaction(3, 2, owner=a)
sb.add_state_assertion('sum', expected_value=0, should_decrypt=True)
sb.add_state_assertion('diff', expected_value=0, should_decrypt=True)
sb.add_transaction('f', user=b)
sb.add_state_assertion('sum', expected_value=5, should_decrypt=True)
sb.add_state_assertion('diff', expected_value=1, should_decrypt=True)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
