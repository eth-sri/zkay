# Optimization example

This is fiddling around with optimizing the stack size such that multiple NIZK proofs can be performed in the same transaction.

It uses the new Zokrates version (GIT commit hash 2b3f50105f14b78196c1bd9ff5d63d96b1d6efd7), whose results only work with the newer solidity compiler version `0.4.25`. Note that the generated verifier contracts have a wrong pragma statement, need to adjust this.

* `truffle-app/` contains the truffle project with the solidity contracts
* `zokrates/` contains zokrates inputs and outputs for a very simple NIZK proof of a root
