from zkay.examples.scenario import ScenarioBuilder
a = 'a'
sb = ScenarioBuilder('NestedPrivateIfStatements', 'code/NestedPrivateIfCond.sol').set_users(a)
sb.set_deployment_transaction(owner=a)
sb.add_balance_assertion(0)

# Test outer private if

sb.add_transaction('test_if_outer', [101], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=1)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)

sb.add_transaction('test_if_outer', [0], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=5)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)

# priv_if(3, 7)
sb.add_transaction('test_if_outer', [1], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=26)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)

# priv_if(123, 87)
sb.add_transaction('test_if_outer', [41], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=36)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)

# priv_if(42, 42)
sb.add_transaction('test_if_outer', [42], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=42)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=True)


# Test inner private if
sb.add_transaction('test_if', [101], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=1)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)

sb.add_transaction('test_if', [0], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=5)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)

# priv_if(3, 7)
sb.add_transaction('test_if', [1], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=26)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)

# priv_if(123, 87)
sb.add_transaction('test_if', [41], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=36)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=False)

# priv_if(42, 42)
sb.add_transaction('test_if', [42], user=a)
sb.add_state_assertion('res', user=a, should_decrypt=True, expected_value=42)
sb.add_state_assertion('val', user=a, should_decrypt=True, expected_value=True)

sb.add_balance_assertion(0)
SCENARIO = sb.build()
