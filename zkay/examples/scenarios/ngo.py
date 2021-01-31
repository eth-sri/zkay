from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

ngo, lobbying, direct_aid, a, b = 'ngo', 'lobbying', 'direct_aid', 'a', 'b'
sb = ScenarioBuilder('NGO', 'code/Ngo.zkay').set_users(ngo, lobbying, direct_aid, a, b)
sb.set_deployment_transaction(lobbying, direct_aid, owner=ngo)

sb.add_transaction('contribute', amount=100, user=a)
sb.add_transaction('contribute', amount=200, user=b)

sb.add_balance_assertion(300)
sb.add_state_assertion('totalContributions', user=ngo, expected_value=300, should_decrypt=True)

# NGO now anonymously pays out money to lobbying / direct_aid, e.g. using the 'TokenHomomorphic' contract
# lobbying & direct_aid confirm having received the contributions

sb.add_transaction('reportReceivedContributions', [150], user=lobbying)
sb.add_transaction('proveMinContributions', user=ngo, expected_exception=RequireException)  # Not yet correct
sb.add_transaction('reportReceivedContributions', [90], user=direct_aid)
sb.add_transaction('proveMinContributions', user=ngo)  # Now it is

SCENARIO = sb.build()
