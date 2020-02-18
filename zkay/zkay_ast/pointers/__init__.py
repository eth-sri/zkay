"""
This package contains modules which resolve references to other AST elements.

==========
Submodules
==========
* :py:mod:`.parent_setter`: Visitor which sets the parent, statement and function references for each element to the correct values.
* :py:mod:`.pointer_exceptions`: Exceptions raised within this module
* :py:mod:`.symbol_table`: Construct symbol table from AST and resolve identifier and user-defined-type targets.
"""