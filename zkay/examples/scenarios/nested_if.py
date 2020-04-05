from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('NestedIfStatements', 'code/NestedIfCond.zkay').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_balance_assertion(0)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=0)

sb.add_transaction('test_if', [51], user=a)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=True)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=2)
sb.add_state_assertion('res2', expected_value=10)

sb.add_transaction('test_if', [43], user=a)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=True)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=3)
sb.add_state_assertion('res2', user=a, expected_value=15)

sb.add_transaction('test_if', [42], user=a)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=3)
sb.add_state_assertion('res2', user=a, expected_value=15)

sb.add_transaction('test_if', [0], user=a)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=4)
sb.add_state_assertion('res2', user=a, expected_value=20)

sb.add_balance_assertion(0)
SCENARIO = sb.build()
