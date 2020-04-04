from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.types import AddressValue
from zkay.zkay_ast.ast import IntTypeName

a = 'a'
sb = ScenarioBuilder('Casting', 'code/Cast.sol').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_balance_assertion(0)

sb.add_transaction('test_signed_casts', user=a)
sb.add_state_assertion('negval', should_decrypt=True, expected_value=-1, plain_type=IntTypeName('int248'))
sb.add_state_assertion('nv2', should_decrypt=True, expected_value=1)
sb.add_state_assertion('pv2', expected_value=-1)
sb.add_state_assertion('pv3', expected_value=(1 << 248)-1)
sb.add_state_assertion('pv4', expected_value=(1 << 248)-1)

sb.add_transaction('f', [378], user=a) # b = false, p = 382, secint = 384, priv_addr = 426,sealed_enum = 1, res = 126
sb.add_state_assertion('p', should_decrypt=True, expected_value=382)
sb.add_state_assertion('priv_addr', should_decrypt=True, expected_value=AddressValue(426))
sb.add_state_assertion('sealed_enum', should_decrypt=True, expected_value=1)
sb.add_state_assertion('res', expected_value=126)

sb.add_transaction('f', [379], user=a) # b = true, p = 2, priv_addr = me, sealed_enum = 2, res = 2
sb.add_state_assertion('p', should_decrypt=True, expected_value=2)
sb.add_state_assertion('sealed_enum', should_decrypt=True, expected_value=2)
sb.add_state_assertion('res', expected_value=2)

sb.add_transaction('f', [(1 << 256)-1], user=a) # b = false, k = 65537, p = 65539, secint = 65541, priv_addr = 65583, sealed_enum = 1, res = 3
sb.add_state_assertion('p', should_decrypt=True, expected_value=65539)
sb.add_state_assertion('priv_addr', should_decrypt=True, expected_value=AddressValue(65583))
sb.add_state_assertion('sealed_enum', should_decrypt=True, expected_value=1)
sb.add_state_assertion('res', expected_value=3)

sb.add_balance_assertion(0)
SCENARIO = sb.build()
