import keyword
from textwrap import dedent
from typing import Union, List, Set

from zkay.zkay_ast.ast import CodeVisitor, Block, IndentBlock, IfStatement, indent, ReturnStatement, Comment, \
    ExpressionStatement, RequireStatement, AssignmentStatement, VariableDeclaration, VariableDeclarationStatement, \
    Array, Mapping, BooleanLiteralExpr, FunctionCallExpr, BuiltinFunction, \
    ElementaryTypeName, TypeName, UserDefinedTypeName, \
    ConstructorOrFunctionDefinition, Parameter, AllExpr, MeExpr, AnnotatedTypeName, ReclassifyExpr, Identifier, \
    SourceUnit, ContractDefinition, Randomness, Key, CipherText, SliceExpr, AddressTypeName, AddressPayableTypeName, \
    StatementList, IdentifierExpr, NewExpr, WhileStatement, ForStatement, BreakStatement, ContinueStatement, DoWhileStatement, \
    EnumDefinition, EnumTypeName, StructTypeName

_kwords = {kw for kw in keyword.kwlist + ['self']}


class PythonCodeVisitor(CodeVisitor):
    """
    Visitor to convert a solidity AST 1:1 to python code.

    This does not generate the additional code necessary for offchain simulation / transaction transformation
    and it also does not support nested local scopes.
    Such functionality is implemented in the PythonOffchainVisitor subclass.
    """

    def __init__(self, replace_with_corresponding_private=False):
        super().__init__(False)
        self.flatten_hybrid_args = replace_with_corresponding_private

    def sanitized(self, name):
        return f'{name}_' if name in self._get_forbidden_words else name

    @property
    def _get_forbidden_words(self) -> Set[str]:
        return _kwords

    def visitSourceUnit(self, ast: SourceUnit):
        return self.visit_list(ast.contracts)

    def visitContractDefinition(self, ast: ContractDefinition):
        raise NotImplementedError("This needs to be implemented in child class")

    def handle_function_params(self, ast: ConstructorOrFunctionDefinition, params: List[Parameter]):
        params = self.visit_list(params, ", ")
        if params:
            return f'self, {params}'
        else:
            return 'self'

    def handle_function_body(self, ast: ConstructorOrFunctionDefinition):
        return self.visit(ast.body)

    def visitBlock(self, ast: Block):
        return self.visitStatementList(ast)

    def visitEnumDefinition(self, ast: EnumDefinition):
        body = '\n'.join([f'{self.visit(val)} = {idx}' for idx, val in enumerate(ast.values)])
        return f'class {self.visit(ast.idf)}(IntEnum):\n{indent(body)}'

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        params = self.handle_function_params(ast, ast.parameters)
        body = self.handle_function_body(ast)
        return f'def {self.sanitized(ast.name)}({params}):\n{indent(body)}'

    def visitStatementList(self, ast: StatementList):
        b = self.visit_list(ast.statements)
        return b if b else 'pass'

    def visitIndentBlock(self, ast: IndentBlock):
        return f'### BEGIN {ast.name}\n{self.visit_list(ast.statements)}\n###  END  {ast.name}'

    def visitIfStatement(self, ast: IfStatement):
        c = self.visit(ast.condition)
        t = self.visit(ast.then_branch)
        ret = f'if {c}:\n{indent(t)}'
        if ast.else_branch:
            e = self.visit(ast.else_branch)
            ret += f'\nelse:\n{indent(e)}'
        return ret

    def visitWhileStatement(self, ast: WhileStatement):
        c = self.visit(ast.condition)
        b = self.visit(ast.body)
        ret = f'while {c}:\n{indent(b)}'
        return ret

    def visitDoWhileStatement(self, ast: DoWhileStatement):
        c = self.visit(ast.condition)
        b = f'{self.visit(ast.body)}\nif not ({c}): break'
        ret = f'while True:\n{indent(b)}'
        return ret

    def visitForStatement(self, ast: ForStatement):
        i = '' if ast.init is None else self.visit(ast.init)
        c = self.visit(ast.condition)
        u = '' if ast.update is None else self.visit(ast.update)
        b = indent(self.visit_single_or_list(ast.body))
        if u:
            b = f'try:\n{b if b else indent("pass")}\nfinally:\n{indent(u)}'
        ret = f'{i}\nwhile {c}:\n{indent(b)}'
        return ret

    def visitBreakStatement(self, _: BreakStatement):
        return 'break'

    def visitContinueStatement(self, _: ContinueStatement):
        return 'continue'

    def visitReturnStatement(self, ast: ReturnStatement):
        e = '' if ast.expr is None else self.visit(ast.expr)
        return f'return {e}'

    def get_default_value(self, t: TypeName) -> str:
        """Return python expression corresponding to the default value of the given type."""
        if isinstance(t, Array) and not isinstance(t, (CipherText, Key, Randomness)):
            expr = t.expr
            if expr is None:
                return '[]'
            else:
                return f'[{self.get_default_value(t.value_type)} for _ in range({self.visit(expr)})]'
        elif isinstance(t, Mapping):
            return '{}'
        elif isinstance(t, EnumTypeName):
            return f'{self.visit_list(t.target.qualified_name, sep=".")}(0)'
        elif isinstance(t, (AddressTypeName, AddressPayableTypeName)):
            return ''
        elif isinstance(t, StructTypeName) and t.target is not None:
            sd = t.target
            s = ''
            for idx, vd in enumerate(sd.members):
                s += f"'{vd.idf.name}': {self.get_default_value(vd.annotated_type.type_name)},"
                s += '\n' if idx % 4 == 3 else ' '
            return f'{{\n{indent(s.rstrip())}\n}}'
        elif isinstance(t, UserDefinedTypeName):
            return '{}'
        else:
            return f'{self.visit(t)}()'

    def handle_var_decl_expr(self, ast: VariableDeclarationStatement) -> str:
        """
        Return python expression corresponding to the variable declaration statement's expression.

        If the declaration has no expression (default initialization in solidity), an expression
        corresponding to the declaration type's default value is returned
        (-> explicit initialization necessary to preserve semantics since python default initializes to undefined).
        """
        t = ast.variable_declaration.annotated_type.type_name
        e = self.get_default_value(t) if ast.expr is None else self.visit(ast.expr)
        return e

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        s = self.visit(ast.variable_declaration)
        e = self.handle_var_decl_expr(ast)
        return f'{s} = {e}'

    def visitExpressionStatement(self, ast: ExpressionStatement):
        return self.visit(ast.expr)

    def visitRequireStatement(self, ast: RequireStatement):
        c = self.visit(ast.condition)
        return dedent(f'''\
            if not ({c}):
                raise RequireException("{ast.unmodified_code[:-1]} failed")''')

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        lhs = ast.lhs
        op = ast.op
        if ast.lhs.annotated_type is not None and ast.lhs.annotated_type.is_private():
            op = ''
        rhs = ast.rhs.args[1] if op else ast.rhs

        if op.startswith(('pre', 'post')):
            op = '+' if op.endswith('++') else '-'

        lhs = self.visit(lhs)
        rhs = self.visit(rhs)
        return f'{lhs} {op}= {rhs}'

    def visitSliceExpr(self, ast: SliceExpr):
        if ast.base is not None:
            base = f'{self.visit(ast.base)} + '
        else:
            base = ''

        return f'{self.visit(ast.arr)}[{base}{ast.start_offset}:{base}{ast.start_offset + ast.size}]'

    def visitNewExpr(self, ast: NewExpr):
        if isinstance(ast.annotated_type.type_name, Array):
            return f'[0 for _ in range({self.visit(ast.args[0])})]'
        else:
            raise NotImplementedError()

    def visitVariableDeclaration(self, ast: Union[VariableDeclaration, Parameter]):
        return f'{self.visit(ast.idf)}: {self.visit(ast.annotated_type)}'

    def visitParameter(self, ast: Parameter):
        return self.visitVariableDeclaration(ast)

    def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
        return f'{ast.value}'

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            args = [self.visit(a) for a in ast.args]
            fstr = ast.func.format_string()
            if ast.func.op == '&&':
                fstr = '{} and {}'
            elif ast.func.op == '||':
                fstr = '{} or {}'
            elif ast.func.op == '!':
                fstr = 'not {}'
            elif ast.func.op == '/':
                fstr = '{} // {}'
            elif ast.func.is_ite():
                fstr = '({1} if {0} else {2})'

            return fstr.format(*args)
        else:
            f = self.visit(ast.func)
            a = self.visit_list(ast.args, ', ')

            if isinstance(ast.func, IdentifierExpr):
                f = f'self.{f}'
            return f'{f}({a})'

    def visitComment(self, ast: Comment):
        return '' if not ast.text else '# ' + ast.text.replace("\n", "\n# ")

    def visitElementaryTypeName(self, ast: ElementaryTypeName):
        if ast.is_numeric:
            return 'int'
        else:
            return ast.code()

    def visitAddressTypeName(self, ast: AddressTypeName):
        return 'str'

    def visitAddressPayableTypeName(self, ast: AddressPayableTypeName):
        return 'str'

    def visitUserDefinedTypeName(self, ast: UserDefinedTypeName):
        return 'Dict'

    def visitEnumTypeName(self, ast: EnumTypeName):
        return f'{self.visit_list(ast.target.qualified_name, sep=".")}'

    def visitMapping(self, ast: Mapping):
        return f'Dict[{self.visit(ast.key_type)}, {self.visit(ast.value_type)}]'

    def visitArray(self, ast: Array):
        return f'List[{self.visit(ast.value_type)}]'

    def visitIdentifier(self, ast: Identifier):
        return self.sanitized(ast.name)

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
        if ast.had_privacy_annotation:
            raise ValueError("Type annotations are not supported for python generation")
        return self.visit(ast.type_name)

    def visitMeExpr(self, _: MeExpr):
        raise ValueError("Me expressions are not supported for python generation")

    def visitAllExpr(self, _: AllExpr):
        raise ValueError("All expressions are not supported for python generation")

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        raise ValueError("Reveal expressions are not supported for python generation")