#!/bin/bash

###########
# PURPOSE #
###########
# Run a simple proof-verification on-chain to determine its gas cost.

# navigate to directory
BASEDIR="$( dirname "$0")"
cd "$BASEDIR"

#########
# CLEAN #
#########

rm -rf ./build scenario.log

#######
# RUN #
#######

# spawn a development blockchain locally, in a background process
temp_file=$(mktemp)
ganache-cli > $temp_file &

# record process id
PID=$!

( tail -f -n0 $temp_file & ) | grep -q "Listening on "

echo "-> ganache-cli is ready!"
echo "   running as process $PID"

# run scenario
truffle compile
truffle migrate | tee "scenario.log"
truffle exec scenario.js | tee -a "scenario.log"
echo "Exit status of scenario: $?"

# kill background process
echo "Waiting for ganache to terminate..."
kill -9 $PID
wait $PID || true

rm $temp_file
