#!/bin/bash
# Run as:
# $ ./compile.sh

# determine directory containing script
BASEDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
cd "$BASEDIR"

source ./prepare.sh

for SOL in "${SOLS[@]}"; do
	DIR="$(dirname "$SOL")"
	TARGET="$DIR/compiled"
	echo "Compiling $SOL to $TARGET"
	python3 "$BPLDIR/main.py" --output "$TARGET" --count-statements "$SOL"
done
