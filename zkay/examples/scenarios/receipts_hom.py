from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

business, a, b, c = 'business', 'a', 'b', 'c'
sb = ScenarioBuilder('ReceiptsHomomorphic', 'code/ReceiptsHomomorphic.zkay').set_users(business, a, b, c)
sb.set_deployment_transaction(owner=business)

sb.add_transaction('receive_receipt', [1, 123], user=a)
sb.add_transaction('give_receipt', [1, 123], user=business)
sb.add_transaction('receive_receipt', [2, 456], user=b)
sb.add_transaction('give_receipt', [2, 456], user=business)
sb.add_transaction('give_receipt', [3, 789], user=business)
sb.add_transaction('receive_receipt', [3, 789], user=c)

sb.add_transaction('check', [1], user=business)
sb.add_transaction('check', [2], user=business)
sb.add_transaction('check', [3], user=business)

SCENARIO = sb.build()
