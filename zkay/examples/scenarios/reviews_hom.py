from zkay.examples.scenario import ScenarioBuilder
from zkay.transaction.offchain import RequireException

pc, r1, r2, r3, author = 'pc', 'r1', 'r2', 'r3', 'author'
sb = ScenarioBuilder('ReviewsHomomorphic', 'code/ReviewsHomomorphic.zkay').set_users(pc, r1, r2, r3, author)
sb.set_deployment_transaction(owner=pc)

sb.add_transaction('registerReviewer', [r1], user=pc)
sb.add_transaction('registerReviewer', [r2], user=pc)
sb.add_transaction('registerReviewer', [r3], user=pc)
sb.add_state_assertion('num_reviewers', expected_value=3)

sb.add_transaction('registerPaper', [1234], user=author)

sb.add_transaction('recordReview', [1234, 3], user=r1)
sb.add_transaction('recordReview', [1234, 2], user=r3)
sb.add_state_assertion('num_reviews', 1234, expected_value=2)
sb.add_state_assertion('sum_of_reviews', 1234, expected_value=5, should_decrypt=True)

sb.add_transaction('decideAcceptance', [author], user=pc)
sb.add_state_assertion('accepted', author, user=author, expected_value=False, should_decrypt=True)

sb.add_transaction('recordReview', [1234, 5], user=r2)
sb.add_state_assertion('num_reviews', 1234, expected_value=3)
sb.add_state_assertion('sum_of_reviews', 1234, expected_value=10, should_decrypt=True)

sb.add_transaction('decideAcceptance', [author], user=pc)
sb.add_state_assertion('accepted', author, user=author, expected_value=True, should_decrypt=True)

SCENARIO = sb.build()
