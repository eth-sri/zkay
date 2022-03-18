#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1], log_filename=sys.argv[2]) as g:
	pc_addr, r1_addr, r2_addr, author_addr = g.create_dummy_accounts(4)

	pc = g.deploy(user=pc_addr)
	r1 = g.connect(pc.address, user=r1_addr)
	r2 = g.connect(pc.address, user=r2_addr)
	author = g.connect(pc.address, user=author_addr)

	pc.registerReviewer(r1_addr)
	pc.registerReviewer(r2_addr)
	author.registerPaper(1234)
	r1.recordReview(1234, 3)
	r2.recordReview(1234, 2)
	pc.decideAcceptance(author_addr)
