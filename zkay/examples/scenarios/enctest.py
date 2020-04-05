from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('RealEncrypt', 'code/EncTest.zkay').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_balance_assertion(0)
sb.add_state_assertion('v', expected_value=0, should_decrypt=True)
sb.add_transaction('test', [42], user=a)
sb.add_state_assertion('v', expected_value=44, should_decrypt=True)
sb.add_balance_assertion(0)
sb.add_transaction('test', [7], user=a)
sb.add_state_assertion('v', expected_value=53, should_decrypt=True)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
