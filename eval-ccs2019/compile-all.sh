#!/bin/bash
# Run as:
# $ ./compile.sh

# determine directory containing script
BASEDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
cd "$BASEDIR"


./list-examples.sh | while read SOL; do
	DIR="$(dirname "$SOL")"
	TARGET="$DIR/compiled"
	echo "Compiling $SOL to $TARGET"
	python3 "$ZKAYSRC/main.py" --output "$TARGET" --count-statements "$SOL"
done
