#!/bin/sh

###########
# PURPOSE #
###########
# Set environment variables necessary to run BPL


# Directory containing this script.
#
# When running `prepare-conda.sh`, this line is
# automatically replaced by a hard-coded path
BASEDIR=$(dirname "$(readlink -f "$0")")

# BPL
export BPLDIR="$BASEDIR/../.."
export BPLSRC="$BPLDIR/src"
export PYTHONPATH="$BPLSRC"


# zokrates
export WITH_LIBSNARK=1
export ZOKRATES_ROOT="$BASEDIR/../ZoKrates"
export ZOKRATES_HOME="$ZOKRATES_ROOT/zokrates_home"
