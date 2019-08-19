#!/bin/bash
# Run as:
# $ ./generate-all-scenarios.sh

# determine directory containing script
BASEDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
cd "$BASEDIR"


./list-examples.sh | while read SOL; do
	DIR="$(dirname "$SOL")"
	echo "Generating scenario for $DIR..."
	./generate-scenario.sh "$DIR"
done
