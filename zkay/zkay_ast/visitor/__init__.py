"""
This package contains several basic AST visitors.

==========
Submodules
==========
* :py:mod:`.deep_copy`: Fast custom deep copy implementation for AST
* :py:mod:`.function_visitor`: Only visits contract functions (mode node-or-children).
* :py:mod:`.python_visitor`: Returns python code corresponding to AST
* :py:mod:`.solidity_visitor`: Returns solidity code corresponding to AST
* :py:mod:`.statement_counter`: Returns number of statements in AST
* :py:mod:`.transformer_visitor`: Visitor base class which replaces visited AST elements by the visit function's return value.
* :py:mod:`.visitor`: AST visitor base class
"""