from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('PublicLoops', 'code/PublicLoops.sol').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_balance_assertion(0)
sb.add_transaction('test', [42], user=a)
sb.add_state_assertion('ret', expected_value=42)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
