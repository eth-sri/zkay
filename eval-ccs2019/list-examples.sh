#!/bin/bash
# Run as:
# $ source ./prepare.sh

# check if activated
if [ -z "$ZKAYSRC" ]; then
	echo "Please run \"conda activate zkay\" first." >&2
	exit 1
fi

while read DIR; do
	SOL="$(find "$DIR" -maxdepth 1 -iname "*.sol" -type f)"
	if [ ! -z "$SOL" ]; then
		# $DIR contains $SOL
		echo "$SOL"
	fi
done < <(find "./examples" -maxdepth 1 -type d)