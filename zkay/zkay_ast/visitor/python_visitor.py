import keyword
from textwrap import dedent
from typing import Union, List

from zkay.zkay_ast.ast import CodeVisitor, Block, IndentBlock, IfStatement, indent, ReturnStatement, Comment, \
    ExpressionStatement, RequireStatement, AssignmentStatement, VariableDeclaration, VariableDeclarationStatement, \
    Array, Mapping, BooleanLiteralExpr, FunctionCallExpr, BuiltinFunction, \
    ElementaryTypeName, TypeName, UserDefinedTypeName, FunctionDefinition, ConstructorDefinition, \
    ConstructorOrFunctionDefinition, Parameter, AllExpr, MeExpr, AnnotatedTypeName, ReclassifyExpr, Identifier, \
    SourceUnit, ContractDefinition, Randomness, Key, CipherText, SliceExpr, AddressTypeName, AddressPayableTypeName, \
    StatementList, IdentifierExpr

kwords = {kw for kw in keyword.kwlist + ['connect', 'deploy', 'help', 'me', 'self']}


def sanitized(name):
    return f'{name}_' if name in kwords else name


class PythonCodeVisitor(CodeVisitor):
    def __init__(self, replace_with_corresponding_private=False):
        super().__init__(False)
        self.follow_private = replace_with_corresponding_private

    def visitSourceUnit(self, ast: SourceUnit):
        return self.visit_list(ast.contracts)

    def visitContractDefinition(self, ast: ContractDefinition):
        raise NotImplementedError("This needs to be implemented in child class")

    def handle_function_params(self, params: List[Parameter]):
        params = self.visit_list(params, ", ")
        if params:
            return f'self, {params}'
        else:
            return 'self'

    def handle_function_body(self, ast: ConstructorOrFunctionDefinition):
        return self.visit(ast.body)

    def visitFunctionDefinition(self, ast: FunctionDefinition):
        return self.visitConstructorOrFunctionDefinition(ast)

    def visitConstructorDefinition(self, ast: ConstructorDefinition):
        return self.visitConstructorOrFunctionDefinition(ast)

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        params = self.handle_function_params(ast.parameters)
        body = self.handle_function_body(ast)
        return f'def {sanitized(ast.name)}({params}):\n{indent(body)}'

    def visitStatementList(self, ast: StatementList):
        return self.visit_list(ast.statements)

    def visitBlock(self, ast: Block):
        return self.visit_list(ast.statements)

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

    def visitReturnStatement(self, ast: ReturnStatement):
        e = '' if ast.expr is None else self.visit(ast.expr)
        return f'return {e}'

    def visitExpressionStatement(self, ast: ExpressionStatement):
        return self.visit(ast.expr)

    def visitRequireStatement(self, ast: RequireStatement):
        c = self.visit(ast.condition)
        return dedent(f'''\
            if not ({c}):
                raise Exception("{ast.code()[:-1]} failed")''')

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        lhs = self.visit(ast.lhs)
        rhs = self.visit(ast.rhs)
        return f'{lhs} = {rhs}'

    def visitSliceExpr(self, ast: SliceExpr):
        return f'{self.visit(ast.arr)}[{ast.start}:{ast.end}]'

    def get_default_value(self, t: TypeName):
        if isinstance(t, Array) and not isinstance(t, (CipherText, Key, Randomness)):
            expr = t.expr
            if expr is None:
                return '[]'
            else:
                return f'[{self.get_default_value(t.value_type)} for _ in range({self.visit(expr)})]'
        elif isinstance(t, Mapping):
            return '{}'
        elif isinstance(t, UserDefinedTypeName):
            return '{}'
        else:
            return f'{self.visit(t)}()'

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        t = ast.variable_declaration.annotated_type.type_name
        s = self.visit(ast.variable_declaration)
        e = self.get_default_value(t) if ast.expr is None else self.visit(ast.expr)
        return f'{s} = {e}'

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
        if ast == TypeName.uint_type():
            return 'int'
        else:
            return ast.code()

    def visitAddressTypeName(self, ast: AddressTypeName):
        return 'str'

    def visitAddressPayableTypeName(self, ast: AddressPayableTypeName):
        return 'str'

    def visitUserDefinedTypeName(self, ast: UserDefinedTypeName):
        return 'Any'

    def visitMapping(self, ast: Mapping):
        return f'Dict[{self.visit(ast.key_type)}, {self.visit(ast.value_type)}]'

    def visitArray(self, ast: Array):
        return f'List[{self.visit(ast.value_type)}]'

    def visitIdentifier(self, ast: Identifier):
        return sanitized(ast.name)

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