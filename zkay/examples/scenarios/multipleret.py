from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('MultipleReturnValues', 'code/MultipleReturnValues.sol').set_users(a)
sb.set_deployment_transaction(owner=a)

sb.add_balance_assertion(0)
for x in [0, 42, 123523]:
    sb.add_transaction('test', [x], user=a)
    sb.add_state_assertion('ret', expected_value=24*x + 134)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
