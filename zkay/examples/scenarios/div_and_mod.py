from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('DivAndMod', 'code/DivAndMod.zkay').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_transaction('testUintDiv', user=a)
sb.add_transaction('testIntDiv', user=a)
sb.add_transaction('testUintMod', user=a)
sb.add_transaction('testIntMod', user=a)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
