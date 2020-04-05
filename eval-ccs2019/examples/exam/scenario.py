#!/usr/bin/env python3
import sys
from zkay.zkay_frontend import transaction_benchmark_ctx

# Scenario
with transaction_benchmark_ctx(sys.argv[1]) as g:
	examinator_addr, student_addr = g.create_dummy_accounts(2)

	examinator = g.deploy(100, user=examinator_addr)
	student = g.connect(examinator.address, user=student_addr)

	examinator.set_solution(1, 12)
	examinator.set_solution(2, 13)
	student.record_answer(1, 12)
	student.record_answer(2, 14)
	examinator.grade_task(1, student_addr)
	examinator.grade_task(2, student_addr)
