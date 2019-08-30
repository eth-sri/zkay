# Convenience wrapper for some quick commands

# run unit tests
unit-test:
	cd src && ../bpl-docker.sh make test

# test compiling & running an example contract
example-contract:
	# compile example contract
	./bpl-docker.sh python3 "./src/main.py" --output ./eval-ccs2019/examples/exam/compiled ./eval-ccs2019/examples/exam/exam.sol
	# generate scenario for example contract
	./bpl-docker.sh ./eval-ccs2019/generate-scenario.sh ./eval-ccs2019/examples/exam
	# run example scenario
	./bpl-docker.sh ./eval-ccs2019/examples/exam/scenario/runner.sh

# run evaluation
evalation:
	./eval-ccs2019/bpl-eval-docker.sh

# test most important commands in repo
test: unit-test example-contract evalation

# generate a zip file of this repository
archive:
	git archive -o bpl.zip HEAD