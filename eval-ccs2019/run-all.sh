#!/bin/bash
# Run as:
# $ ./compile.sh

# determine directory containing script
BASEDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
cd "$BASEDIR"

./list-examples.sh | while read SOL; do
	DIR="$(dirname "$SOL")"
	RUNNER="$DIR/scenario/runner.sh"
	echo -e "\n\nRunning $RUNNER\n\n"
	bash "$RUNNER"
done
