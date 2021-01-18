from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

a, b, c = 'a', 'b', 'c'
sb = ScenarioBuilder('TokenHomomorphic', 'code/TokenHomomorphic.zkay').set_users(a, b, c)
sb.set_deployment_transaction(owner=a)
sb.add_transaction('register', user=a)
sb.add_transaction('register', user=b)
sb.add_transaction('register', user=c)

sb.add_transaction('buy', [100], user=a)
sb.add_state_assertion('balance', a, user=a, expected_value=100, should_decrypt=True)
sb.add_transaction('buy', [50], user=b)
sb.add_state_assertion('balance', b, user=b, expected_value=50, should_decrypt=True)

sb.add_transaction('send_tokens', [40, c], user=a)
sb.add_state_assertion('balance', a, user=a, expected_value=60, should_decrypt=True)
sb.add_state_assertion('balance', c, user=c, expected_value=40, should_decrypt=True)

sb.add_transaction('send_tokens', [50, b], user=c, expected_exception=RequireException)
sb.add_state_assertion('balance', a, user=a, expected_value=60, should_decrypt=True)
sb.add_state_assertion('balance', b, user=b, expected_value=50, should_decrypt=True)
sb.add_state_assertion('balance', c, user=c, expected_value=40, should_decrypt=True)

SCENARIO = sb.build()
