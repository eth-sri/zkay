"""
This package contains the runtime API used by the offchain simulation code when working with zkay transactions.

==========
Submodules
==========
* :py:mod:`.interface`: Runtime API interface
* :py:mod:`.offchain`: Offchain simulator base class with common functionality
* :py:mod:`.runtime`: Static class which provides access to the individual API backend singletons.
* :py:mod:`.types`: Type wrapper classes (for safer API interactions) used by the Runtime API.

===========
Subpackages
===========
* :py:mod:`.blockchain`: Blockchain backends
* :py:mod:`.crypto`: Cipher backends
* :py:mod:`.keystore`: Keystore backends
* :py:mod:`.prover`: Proof-generation backends
"""