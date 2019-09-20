# Convenience wrapper for some quick commands

# run unit tests
unit-test:
	./zkay-docker.sh make -C src test

# test compiling & running an example contract
example-contract:
	# compile example contract
	./zkay-docker.sh python3 "./src/main.py" --output ./eval-ccs2019/examples/exam/compiled ./eval-ccs2019/examples/exam/exam.sol
	# generate scenario for example contract
	./zkay-docker.sh ./eval-ccs2019/generate-scenario.sh ./examples/exam
	# run example scenario
	./zkay-docker.sh ./eval-ccs2019/examples/exam/scenario/runner.sh

# run evaluation
evalation:
	./eval-ccs2019/zkay-eval-docker.sh

# test most important commands in repo
test: unit-test example-contract evalation

# remove all gitignored files
clean:
	git clean -x -d -f