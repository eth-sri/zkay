from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('Rehom', 'code/RehomArgs.zkay').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_transaction('add_hom', [2], user=a)
sb.add_state_assertion('y', expected_value=2, should_decrypt=True)
sb.add_transaction('un_hom', [3], user=a)
sb.add_state_assertion('z', expected_value=3, should_decrypt=True)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
