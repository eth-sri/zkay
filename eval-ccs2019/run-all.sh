#!/bin/bash
# Run as:
# $ ./compile.sh

# determine directory containing script
BASEDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
cd "$BASEDIR"

source ./prepare.sh

for SOL in "${SOLS[@]}"; do
	DIR="$(dirname "$SOL")"
	RUNNER="$DIR/scenario/runner.sh"
	echo -e "\n\nRunning $RUNNER\n\n"
	bash "$RUNNER"
done
