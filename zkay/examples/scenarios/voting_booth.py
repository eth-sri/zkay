from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

owner, a, b, c = 'owner', 'a', 'b', 'c'
sb = ScenarioBuilder('VotingBooth', 'code/VotingBooth.zkay').set_users(owner, a, b, c)
sb.set_deployment_transaction(owner=owner)

sb.add_transaction('vote', [0], user=a)  # A votes for A
sb.add_transaction('vote', [1], user=b)  # B votes for B
sb.add_transaction('vote', [1], user=c)  # C votes for B
sb.add_transaction('vote', [0], user=a, expected_exception=RequireException)  # No double-voting

sb.add_state_assertion('votesForA', user=owner, expected_value=1, should_decrypt=True)
sb.add_state_assertion('votesForB', user=owner, expected_value=2, should_decrypt=True)

sb.add_transaction('declareWinner', user=a, expected_exception=RequireException)  # Only owner can call the vote
sb.add_transaction('declareWinner', user=owner)

sb.add_transaction('vote', [0], user=a, expected_exception=RequireException)  # No voting after the vote was called

SCENARIO = sb.build()
