import inspect

from zkay.zkay_ast.ast import AST
from zkay.zkay_ast.pointers.parent_setter import set_parents
from zkay.zkay_ast.pointers.symbol_table import link_identifiers
from zkay.zkay_ast.visitor.visitor import AstVisitor


def deep_copy(ast: AST):
    """

    :param ast:
    :return: a deep copy of `ast`

    Only parents and identifiers are updated in the returned ast (e.g., inferred types are not preserved)
    """
    v = DeepCopyVisitor()
    ast_copy = v.visit(ast)
    ast_copy.parent = ast.parent
    set_parents(ast_copy)
    link_identifiers(ast_copy)
    return ast_copy


class DeepCopyVisitor(AstVisitor):

    def __init__(self):
        super().__init__('node-or-children')

    def visitChildren(self, ast):
        c = ast.__class__
        args_names = inspect.getfullargspec(c.__init__).args[1:]
        new_fields = {}
        for arg_name in args_names:
            old_field = getattr(ast, arg_name)
            new_fields[arg_name] = self.copy_field(old_field)

        setting_later = [
            # General fields
            'line',
            'column',

            # Specialized fields
            'parent',
            'names',
            'had_privacy_annotation',
            'annotated_type',
            'statement',
            'before_analysis',
            'after_analysis',
            'target',
            'instantiated_key',
            'function',
            'is_private',
        ]
        for k in ast.__dict__.keys():
            if k not in new_fields and k not in setting_later:
                raise ValueError("Not copying", k)
        ast_copy = c(**new_fields)
        ast_copy.line = ast.line
        ast_copy.column = ast.column
        return ast_copy

    def visitAnnotatedTypeName(self, ast):
        ast_copy = self.visitChildren(ast)
        ast_copy.had_privacy_annotation = ast.had_privacy_annotation
        return ast_copy

    def copy_field(self, field):
        if field is None:
            return None
        elif isinstance(field, str) or isinstance(field, int) or isinstance(field, bool):
            return field
        elif isinstance(field, list):
            return [self.copy_field(e) for e in field]
        else:
            return self.visit(field)