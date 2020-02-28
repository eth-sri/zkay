"""
This module contains the definitions of all exceptions which may be publicly raised by zkay
"""


class ZkayCompilerError(Exception):
    """
    Error during compilation
    """
    pass


class ZkaySyntaxError(ZkayCompilerError):
    """
    Error during parsing / AST construction"
    """


class PreprocessAstException(ZkayCompilerError):
    """
    Error during ast pre-processing"
    """
    pass


class TypeCheckException(ZkayCompilerError):
    """
    Error during type checking"
    """
    pass
