"""
The main zkay package.

==========
Submodules
==========
* :py:mod:`.__main__`: Zkay command line interface
* :py:mod:`.config`: Global zkay configuration (both user-configuration as well as zkay-internal configuration)

===========
Subpackages
===========
* :py:mod:`.compiler`: Internal compilation functionality
* :py:mod:`.errors`: Defines exceptions which may be raised by public zkay interfaces
* :py:mod:`.jsnark_interface`: Glue code for interacting with the external jsnark and libsnark interfaces
* :py:mod:`.my_logging`: Logging facilities
* :py:mod:`.transaction`: Runtime API (used by the auto-generated offchain transaction simulator classes)
* :py:mod:`.type_check`: Internal type-checking and program analysis functionality
* :py:mod:`.utils`: Internal helper functionality
* :py:mod:`.zkay_ast`: AST-related functionality
"""