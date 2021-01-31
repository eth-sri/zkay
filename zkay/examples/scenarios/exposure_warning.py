from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

hospital, a, a_inf, b, b_inf, c = 'hospital', 'a', 'a_inf', 'b', 'b_inf', 'c'
sb = ScenarioBuilder('ExposureWarning', 'code/ExposureWarning.zkay').set_users(hospital, a, a_inf, b, b_inf, c)
sb.set_deployment_transaction(owner=hospital)

sb.add_transaction('setInfected', [a_inf], user=hospital)
sb.add_transaction('setInfected', [b_inf], user=hospital)
sb.add_transaction('setInfected', [c], user=b, expected_exception=RequireException)

sb.add_state_assertion('is_infected', a_inf, expected_value=True)
sb.add_state_assertion('is_infected', b_inf, expected_value=True)
sb.add_state_assertion('is_infected', c, expected_value=False)

# a had contact with b and c; b had contact with c
sb.add_transaction('notifyAboutExposure', [b], user=a_inf)
sb.add_transaction('notifyAboutExposure', [c], user=a_inf)
sb.add_transaction('notifyAboutExposure', [c], user=b_inf)
sb.add_transaction('notifyAboutExposure', [a], user=c, expected_exception=RequireException)

sb.add_state_assertion('exposures', a, user=a, expected_value=0, should_decrypt=True)
sb.add_state_assertion('exposures', b, user=b, expected_value=1, should_decrypt=True)
sb.add_state_assertion('exposures', c, user=c, expected_value=2, should_decrypt=True)

SCENARIO = sb.build()
