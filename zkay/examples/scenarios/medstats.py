from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

hospital, patient1, patient2 = 'hospital', 'patient1', 'patient2'
sb = ScenarioBuilder('MedStats', 'code/MedStats.sol').set_users(hospital, patient1, patient2)
# Set hospital as owner
sb.set_deployment_transaction(owner=hospital)

# Initial state clean
sb.add_balance_assertion(0)
sb.add_state_assertion('risk', patient1, user=patient1, should_decrypt=True, expected_value=False)
sb.add_state_assertion('risk', patient2, user=patient2, should_decrypt=True, expected_value=False)

# Add record for patient 1
sb.add_transaction('record', [patient1, True], user=hospital)
sb.add_state_assertion('risk', patient1, user=patient1, should_decrypt=True, expected_value=True)
sb.add_state_assertion('risk', patient2, user=patient2, should_decrypt=True, expected_value=False)

# Add record for patient 2
sb.add_transaction('record', [patient2, False], user=hospital)
sb.add_state_assertion('risk', patient1, user=patient1, should_decrypt=True, expected_value=True)
sb.add_state_assertion('risk', patient2, user=patient2, should_decrypt=True, expected_value=False)

# Patient 1 tries to tamper but can't
sb.add_transaction('record', [patient1, False], user=patient1, expected_exception=RequireException)
sb.add_transaction('record', [patient2, True], user=patient1, expected_exception=RequireException)
sb.add_state_assertion('risk', patient1, user=patient1, should_decrypt=True, expected_value=True)
sb.add_state_assertion('risk', patient2, user=patient2, should_decrypt=True, expected_value=False)

# Check that checking works
sb.add_transaction('check', [True], user=patient1)
sb.add_transaction('check', [False], user=patient1, expected_exception=RequireException)
sb.add_transaction('check', [True], user=patient2, expected_exception=RequireException)
sb.add_transaction('check', [False], user=patient2)

# Check that correct state in the end
sb.add_state_assertion('risk', patient1, user=patient1, should_decrypt=True, expected_value=True)
sb.add_state_assertion('risk', patient2, user=patient2, should_decrypt=True, expected_value=False)
sb.add_balance_assertion(0)
SCENARIO = sb.build()
