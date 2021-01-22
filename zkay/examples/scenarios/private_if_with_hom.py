from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('PrivateIfWithHom', 'code/PrivateIfWithHom.zkay').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_transaction('f', [True, 1, 2], user=a)
sb.add_state_assertion('a', expected_value=1, should_decrypt=True)
sb.add_state_assertion('b', expected_value=1, should_decrypt=True)
sb.add_transaction('f', [False, 1, 2], user=a)
sb.add_state_assertion('a', expected_value=2, should_decrypt=True)
sb.add_state_assertion('b', expected_value=2, should_decrypt=True)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
