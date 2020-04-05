from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('SimpleAddition', 'code/Addition.zkay').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_transaction('f', [1, 2], user=a)
sb.add_state_assertion('x', expected_value=3)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
