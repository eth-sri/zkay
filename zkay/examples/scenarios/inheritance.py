from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

owner, a, b, c, d = 'owner', 'a', 'b', 'c', 'd'
sb = ScenarioBuilder('Inheritance', 'code/Inheritance.zkay').set_users(owner, a, b, c, d)
sb.set_deployment_transaction(owner=owner)

sb.add_transaction('register', user=a)
sb.add_transaction('register', user=b)
sb.add_transaction('register', user=c)
sb.add_transaction('register', user=d)

sb.add_transaction('buy', amount=100, user=a)
sb.add_transaction('buy', amount=100, user=b)
sb.add_transaction('buy', amount=100, user=c)
sb.add_transaction('buy', amount=100, user=d)
sb.add_balance_assertion(400)

# A pledges 50 to B, 50 to C (after failing to give 100 to C due to missing funds)
sb.add_transaction('pledge_inheritance', [b, 50], user=a)
sb.add_transaction('pledge_inheritance', [c, 100], user=a, expected_exception=RequireException)
sb.add_transaction('pledge_inheritance', [c, 50], user=a)
sb.add_state_assertion('inheritance_pledged_send', a, b, user=a, expected_value=50, should_decrypt=True)
sb.add_state_assertion('inheritance_pledged_send', a, c, user=a, expected_value=50, should_decrypt=True)

# B pledges 50 to A, 50 to C
sb.add_transaction('pledge_inheritance', [a, 50], user=b)
sb.add_transaction('pledge_inheritance', [c, 50], user=b)
sb.add_state_assertion('inheritance_pledged_send', b, a, user=b, expected_value=50, should_decrypt=True)
sb.add_state_assertion('inheritance_pledged_send', b, c, user=b, expected_value=50, should_decrypt=True)

# B cannot claim their inheritance from A as A is still marked as alive
sb.add_transaction('claim_inheritance', [a], user=b, expected_exception=RequireException)

# A fails to report in, assumed dead
sb.add_transaction('_test_advance_time', user=owner)
sb.add_transaction('keep_alive', user=b)

# B and C can now claim their inheritance
sb.add_transaction('claim_inheritance', [a], user=b)
sb.add_transaction('claim_inheritance', [a], user=c)
sb.add_state_assertion('balance', a, user=a, expected_value=0, should_decrypt=True)
sb.add_state_assertion('balance', b, user=b, expected_value=150, should_decrypt=True)
sb.add_state_assertion('balance', c, user=c, expected_value=150, should_decrypt=True)

# Double claim or claim when nothing pledged -> no-op
sb.add_transaction('claim_inheritance', [a], user=b)
sb.add_transaction('claim_inheritance', [a], user=d)
sb.add_state_assertion('balance', a, user=a, expected_value=0, should_decrypt=True)
sb.add_state_assertion('balance', b, user=b, expected_value=150, should_decrypt=True)
sb.add_state_assertion('balance', d, user=d, expected_value=100, should_decrypt=True)

# B removes pledge to A, changes pledge to 50 to D, 100 to C
sb.add_transaction('pledge_inheritance', [a, 0], user=b)
sb.add_transaction('pledge_inheritance', [d, 50], user=b)
sb.add_transaction('pledge_inheritance', [c, 100], user=b)

# B fails to report in, assumed dead
sb.add_transaction('_test_advance_time', user=owner)

# C claims the inheritance, D does not
sb.add_transaction('claim_inheritance', [b], user=c)
sb.add_state_assertion('balance', c, user=c, expected_value=250, should_decrypt=True)
sb.add_state_assertion('balance', b, user=b, expected_value=50, should_decrypt=True)

SCENARIO = sb.build()
