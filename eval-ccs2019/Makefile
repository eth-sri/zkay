
# ensure to run `source activate.sh` before running these targets

CODE=../code
EVAL=../paper/eval

compile:
	./compile-all.sh

scenarios: compile
	./generate-all-scenarios.sh

run-scenarios:
	./run-all.sh

analyze:
	PYTHONPATH=$(CODE):. python ./plot/analyze.py
	cp ./plot/*.csv ./plot/*.pdf $(EVAL)
	pdfcrop $(EVAL)/MedStats_costs.pdf $(EVAL)/MedStats_costs.pdf
	pdfcrop $(EVAL)/transaction_costs.pdf $(EVAL)/transaction_costs.pdf

# requires: sudo apt-get -y install cloc
loc:
	cloc --git --by-file --include-lang=Python --not-match-d='ZoKrates|generated' --fullpath $(CODE) | tee $(EVAL)/loc.txt

eval: loc scenarios run-scenarios analyze

