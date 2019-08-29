#!/bin/bash

###########
# PURPOSE #
###########
# Generate contract and proof to estimate cost

BASEDIR="$(dirname "$(readlink -f "$0")")"
cd "$BASEDIR"

SCHEME=gm17

# compile
$ZOKRATES_ROOT/zokrates compile -i minimal.code
# perform the setup phase
$ZOKRATES_ROOT/zokrates setup --proving-scheme $SCHEME
# execute the program
$ZOKRATES_ROOT/zokrates compute-witness -a 0
# generate a proof of computation
$ZOKRATES_ROOT/zokrates generate-proof --proving-scheme $SCHEME
# export a solidity verifier
$ZOKRATES_ROOT/zokrates export-verifier --proving-scheme $SCHEME

cp verifier.sol ../run/contracts

PROOF=../run/proof.js
rm -f $PROOF
echo "module.exports = { proof:" >> $PROOF
cat proof.json >> $PROOF
echo "}" >> $PROOF