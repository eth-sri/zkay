from zkay.examples.scenario import ScenarioBuilder
a, b = 'a', 'b'
sb = ScenarioBuilder('SharedProd', 'code/SharedProd.zkay').set_users(a, b)
sb.set_deployment_transaction(owner=a)
sb.add_state_assertion('secret', expected_value=3, should_decrypt=True)
sb.add_transaction('foo', [4], user=b)
sb.add_transaction('foo', [5], user=a)
sb.add_state_assertion('secret', expected_value=60, should_decrypt=True)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
