from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

raiser, backer1, backer2 = 'hospital', 'patient1', 'patient2'
sb = ScenarioBuilder('CrowdFundingSuccess', 'code/CrowdFunding.zkay').set_users(raiser, backer1, backer2)
# Set hospital as owner
sb.set_deployment_transaction(100, 3600, amount=20, owner=raiser)
sb.add_balance_assertion(20)
sb.add_state_assertion('pot_balance', user=raiser, should_decrypt=True, expected_value=20)
sb.add_state_assertion('pledged', raiser, user=raiser, should_decrypt=True, expected_value=20)

# Add some money to the contract
sb.add_transaction('fund', user=backer1, amount=300)
sb.add_transaction('fund', user=backer2, amount=2000)
sb.add_balance_assertion(2320)
sb.add_state_assertion('pot_balance', user=raiser, should_decrypt=True, expected_value=20)
sb.add_state_assertion('funds', backer1, user=backer1, should_decrypt=True, expected_value=300)
sb.add_state_assertion('funds', backer2, user=backer2, should_decrypt=True, expected_value=2000)

# Ooops, correct mistake
sb.add_transaction('retrieve_unpledged_funds', user=backer2)
sb.add_state_assertion('funds', backer2, user=backer2, should_decrypt=True, expected_value=0)
sb.add_balance_assertion(320)
sb.add_transaction('fund', user=backer2, amount=500)
sb.add_state_assertion('funds', backer2, user=backer2, should_decrypt=True, expected_value=500)
sb.add_balance_assertion(820)

# This should fail since nothing is pledged yet
sb.add_transaction('accept_pledge', user=raiser, expected_exception=RequireException)

# Pledge money 1
sb.add_transaction('pledge', [50], user=backer1)
sb.add_state_assertion('funds', backer1, user=backer1, should_decrypt=True, expected_value=250)
sb.add_state_assertion('pledged', backer1, user=backer1, should_decrypt=True, expected_value=50)

# This should fail since pending
sb.add_transaction('pledge', [50], user=backer1, expected_exception=RequireException)

# Accept money 1
sb.add_transaction('accept_pledge', user=raiser)
sb.add_balance_assertion(820)
sb.add_state_assertion('pot_balance', user=raiser, should_decrypt=True, expected_value=70)
sb.add_state_assertion('success', user=raiser, expected_value=False)
sb.add_state_assertion('closed', user=raiser, expected_value=False)

# Pledge money 2
sb.add_transaction('pledge', [10], user=backer1)
sb.add_state_assertion('funds', backer1, user=backer1, should_decrypt=True, expected_value=240)
sb.add_state_assertion('pledged', backer1, user=backer1, should_decrypt=True, expected_value=60)

# Accept money 2
sb.add_transaction('accept_pledge', user=raiser)
sb.add_balance_assertion(820)
sb.add_state_assertion('pot_balance', user=raiser, should_decrypt=True, expected_value=80)
sb.add_state_assertion('success', user=raiser, expected_value=False)
sb.add_state_assertion('closed', user=raiser, expected_value=False)

# Pledge money 3
sb.add_transaction('pledge', [200], user=backer2)
sb.add_state_assertion('funds', backer2, user=backer2, should_decrypt=True, expected_value=300)
sb.add_state_assertion('pledged', backer2, user=backer2, should_decrypt=True, expected_value=200)

# Try to refund which is impossible since not closed without success
sb.add_transaction('request_refund', user=backer2, expected_exception=RequireException)
sb.add_transaction('accept_pledge', user=backer2, expected_exception=RequireException)

# Collection also not yet possible since not closed
sb.add_transaction('collect_pot', user=raiser, expected_exception=RequireException)

# Drain funds early
sb.add_transaction('retrieve_unpledged_funds', user=backer1)
sb.add_state_assertion('funds', backer1, user=backer1, should_decrypt=True, expected_value=0)
sb.add_state_assertion('pledged', backer1, user=backer1, should_decrypt=True, expected_value=60)
sb.add_balance_assertion(580)

# Accept money 3
sb.add_transaction('accept_pledge', user=raiser)
sb.add_balance_assertion(580)
sb.add_state_assertion('pot_balance', user=raiser, should_decrypt=True, expected_value=280)
sb.add_state_assertion('success', user=raiser, expected_value=True)
sb.add_state_assertion('closed', user=raiser, expected_value=True)

# Drain funds
sb.add_transaction('retrieve_unpledged_funds', user=backer2)
sb.add_state_assertion('funds', backer2, user=backer2, should_decrypt=True, expected_value=0)
sb.add_state_assertion('pledged', backer2, user=backer2, should_decrypt=True, expected_value=200)
sb.add_balance_assertion(280)

# No you cannot steal and you cannot get out
sb.add_transaction('collect_pot', user=backer2, expected_exception=RequireException)
sb.add_transaction('refund_everyone', user=backer2, expected_exception=RequireException)
sb.add_transaction('request_refund', user=backer2, expected_exception=RequireException)

# Too late to close and refund
sb.add_transaction('refund_everyone', user=raiser, expected_exception=RequireException)

sb.add_state_assertion('pot_balance', user=raiser, should_decrypt=True, expected_value=280)
sb.add_balance_assertion(280)
sb.add_transaction('collect_pot', user=raiser)
sb.add_balance_assertion(0)

sb.add_transaction('request_refund', user=backer2, expected_exception=RequireException)
sb.add_transaction('collect_pot', user=raiser)
sb.add_balance_assertion(0)

SCENARIO = sb.build()
