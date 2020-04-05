from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('FuncCalls', 'code/FuncCalls.zkay').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_balance_assertion(0)
sb.add_transaction('compute', [42, 5], user=a)
sb.add_state_assertion('res', expected_value=326020380, should_decrypt=True)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
