#!/bin/sh

###########
# PURPOSE #
###########
# Set environment variables necessary to run zkay


# Directory containing this script.
#
# When running `prepare-conda.sh`, this line is
# automatically replaced by a hard-coded path
BASEDIR=$(dirname "$(readlink -f "$0")")

# zkay
export ZKAYDIR="$BASEDIR/../.."
export ZKAYSRC="$ZKAYDIR/src"
export PYTHONPATH="$ZKAYSRC"


# zokrates
export WITH_LIBSNARK=1
export ZOKRATES_ROOT="$BASEDIR/../ZoKrates"
export ZOKRATES_HOME="$ZOKRATES_ROOT/zokrates_home"
