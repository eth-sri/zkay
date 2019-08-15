#!/bin/bash
# Run as:
# $ source ./prepare.sh

# check if activated
if [ -z "$BPLDIR" ]; then
	echo "Please run \"REPOSITORY_ROOT/code/activate.sh\" first." >&2
	exit 1
fi

SOLS=()

while read DIR; do
	SOL="$(find "$DIR" -maxdepth 1 -iname "*.sol" -type f)"
	if [ ! -z "$SOL" ]; then
		# $DIR contains $SOL
		SOLS+=("$SOL")
	fi
done < <(find "./examples" -maxdepth 1 -type d)