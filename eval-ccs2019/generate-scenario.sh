#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Illegal number of arguments. Usage: ./generate-scenario.sh \"/path/to/directory\"" >&2
	exit 1
fi

# determine directory containing script
BASEDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
cd "$BASEDIR"

source ./prepare.sh

PYTHONPATH="$BPLDIR:$BASEDIR" python3 "$1/scenario.py"