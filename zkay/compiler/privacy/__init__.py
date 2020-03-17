"""
This package deals with zkay compilation.

==========
Submodules
==========
* :py:mod:`.library_contracts`: Stores strings which contain pki and library contract solidity code
* :py:mod:`.manifest` Defines the entries of the zkay manifest file which stores compilation metadata.
* :py:mod:`.offchain_compiler` Offchain simulation code generator.

===========
Subpackages
===========
* :py:mod:`.transformation`: Contains modules for transforming zkay ASTs into solidity ASTs + abstract proof circuits
* :py:mod:`.circuit_generation`: Contains modules for compiling abstract proof circuits into backend specific representations.
* :py:mod:`.proving_scheme`: Contains modules for generating verification contracts for different proving schemes.
"""