from random import Random

from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

rng = Random(1)  # Static seed for testing


def rand():
    return rng.randint(-(1 << 63), (1 << 63) - 1)


def rand_3():
    return [rand(), rand(), rand()]


owner, c1, c2, c3, a, b, c = 'owner', 'c1', 'c2', 'c3', 'a', 'b', 'c'
sb = ScenarioBuilder('Referendum', 'code/Referendum.zkay').set_users(owner, c1, c2, c3, a, b, c)
sb.set_deployment_transaction(c1, c2, c3, owner=owner)

sb.add_transaction('vote', [-1] + rand_3(), user=a)  # A votes Nay
sb.add_transaction('vote', [1] + rand_3(), user=b)  # B votes Nay
sb.add_transaction('vote', [0] + rand_3(), user=c, expected_exception=RequireException)  # Invalid vote
sb.add_transaction('vote', [1] + rand_3(), user=c)  # C votes Yay
sb.add_transaction('vote', [1] + rand_3(), user=a, expected_exception=RequireException)  # No double-voting

sb.add_transaction('countVotes', user=a, expected_exception=RequireException)  # Not a vote-counter
sb.add_transaction('countVotes', user=c1)
sb.add_transaction('countVotes', user=c2)
sb.add_transaction('countVotes', user=c3)

sb.add_transaction('getResult', user=a)
sb.add_state_assertion('combinedResult', expected_value=1)

SCENARIO = sb.build()
