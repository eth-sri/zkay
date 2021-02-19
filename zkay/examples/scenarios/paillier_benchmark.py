from zkay.examples.scenario import ScenarioBuilder

a = 'a'
sb = ScenarioBuilder('PaillierBenchmark', 'code/PaillierBenchmark.zkay').set_users(a)
sb.set_deployment_transaction(owner=a)
SCENARIO = sb.build()
