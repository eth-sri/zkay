# Convenience wrapper for some quick commands

# build zkay package
build:
	python3 setup.py sdist

# install Python dependencies
install-requires:
	pip3 install -r ./install/requirements.txt

# install latest built zkay package if not already installed (no-binary as wheel build currently not supported)
install: build install-requires
	ls -Art dist/zkay-*.tar.gz | tail -n 1 | xargs pip3 install zkay --no-index --no-binary zkay --find-links

# install zkay in dev mode (i.e. symlinked into pip site-packages)
develop:
	pip3 install -e .

# run unit tests
test: install
	cd zkay && python3 -m unittest discover --verbose zkay.tests && cd ..

# test compiling & running an example contract
example-contract: install
	# compile example contract
	zkay compile -o ./eval-ccs2019/examples/exam/compiled ./eval-ccs2019/examples/exam/exam.zkay
	# enter transaction interface in eth-tester mode (local test chain)
	zkay run --blockchain-backend w3-eth-tester ./eval-ccs2019/examples/exam/compiled

# run evaluation
evalation: install
	python3 ./eval-ccs2019/benchmark.py; \
	python3 ./eval-ccs2019/extract_results.py

# remove all gitignored files
clean:
	git clean -x -d -f
