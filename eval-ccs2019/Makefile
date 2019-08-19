
# compile all examples
compile:
	./compile-all.sh

# generate all scenarios pre-defined in python
scenarios: compile
	./generate-all-scenarios.sh

# run all generated scenarios
run-scenarios:
	./run-all.sh

analyze:
	PYTHONPATH=$(BPLSRC):. python ./plot/analyze.py
	pdfcrop ./plot/MedStats_costs.pdf ./plot/MedStats_costs_cropped.pdf
	pdfcrop ./plot/transaction_costs.pdf ./plot/transaction_costs_cropped.pdf

# requires: sudo apt-get -y install cloc
loc:
	cloc --git --by-file --include-lang=Python --not-match-d='ZoKrates|generated' --fullpath $(BPLSRC) | tee ./loc.txt

# run all targets (full evaluation)
eval: loc scenarios run-scenarios analyze
