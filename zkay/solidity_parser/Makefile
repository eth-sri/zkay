SHELL=/bin/bash

all: grammar

grammar: clean
	antlr4 -visitor -Dlanguage=Python3 -o generated Solidity.g4

test: grammar
	bash -c "cd ..; source ./activate.sh; python -m unittest solidity_parser/*.py"

clean:
	rm -rf generated
