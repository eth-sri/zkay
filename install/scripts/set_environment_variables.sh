#!/bin/sh

###########
# PURPOSE #
###########
# Set environment variables necessary to run BPL


# directory containing this script
BASEDIR=$(dirname "$(readlink -f "$0")")

# BPL
export BPLDIR="$BASEDIR/../.."
export PYTHONPATH="$BPLDIR"


# zokrates
export WITH_LIBSNARK=1
export ZOKRATES_ROOT="$BASEDIR/../ZoKrates"
export ZOKRATES_HOME="$ZOKRATES_ROOT/zokrates_home"
