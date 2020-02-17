"""
This module contains the definitions of all exceptions which may be publicly raised by zkay
"""


class ZkayCompilerError(Exception):
    pass


class ParseExeception(ZkayCompilerError):
    """
    Error during parsing"
    """
    pass


class PreprocessAstException(ZkayCompilerError):
    """
    Error during ast preprocessing"
    """
    pass


class TypeCheckException(ZkayCompilerError):
    """
    Error during type checking"
    """
    pass
