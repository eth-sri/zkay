"""
This package deals with solidity/solc compilation.

==========
Submodules
==========
* :py:mod:`.compiler`: Type-check or compile solidity code (uses standard_json interface internally).
* :py:mod:`.fake_solidity_generator`: Strip privacy features from zkay in a source-code location preserving way, so that type-checking/analysis can be performed with tools designed for solidity code.
"""