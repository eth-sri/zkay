from typing import Dict, Union, List

from zkay_ast.ast import FunctionCallExpr, BuiltinFunction, BooleanLiteralExpr, NumberLiteralExpr, \
    ReclassifyExpr, AllExpr, MeExpr, ReturnStatement, RequireStatement, AssignmentStatement, Block, TypeName, \
    VariableDeclaration, FunctionDefinition, IdentifierExpr, VariableDeclarationStatement, ConstructorDefinition, \
    Expression, AST, AnnotatedTypeName, StateVariableDeclaration, ContractDefinition, Mapping, \
    ConstructorOrFunctionDefinition, Parameter, Identifier
from zkay_ast.visitor.visitor import AstVisitor


class Simulator(AstVisitor):

    def __init__(self):
        super().__init__(None)
        self.location_getter = LocationGetter(self)

        # set later by call
        self.state: Dict = {}
        self.me: str = None
        self.return_value = None
        self.parameters: List = None
        self.values: Dict[Union[Parameter, Expression], object] = None
        self.owners: Dict[Union[Parameter, Expression], str] = None

    def visit(self, ast: AST):
        f = self.get_visit_function(ast.__class__)
        if f:
            ret = f(ast)
            if isinstance(ast, Expression) and ast.parent is not None and not isinstance(ast.parent, AnnotatedTypeName):
                self.values[ast] = ret

                if ast.annotated_type:
                    privacy = ast.annotated_type.privacy_annotation
                    self.owners[ast] = self.visit_privacy_annotation(privacy)
            return ret
        else:
            raise NotImplementedError(ast.__class__, ast)

    def visit_privacy_annotation(self, expr: Expression):
        label = expr.privacy_annotation_label()
        if isinstance(label, Identifier):
            return self.state[label.parent]
        else:
            return self.visit(label)

    def call(self, f: ConstructorOrFunctionDefinition, me: str, parameters: List):
        self.me = me
        self.return_value = None
        self.parameters = parameters
        self.values = {}
        self.owners = {}
        return self.visit(f)

    def evaluate(self, state: Dict, expr: Expression, me: str):
        self.state = state
        self.me = me
        self.values = {}
        self.owners = {}
        return self.visit(expr)

    def state_by_name(self):
        ret = {}
        for k, v in self.state.items():
            assert (isinstance(k, StateVariableDeclaration))
            ret[k.idf.name] = v
        return ret

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        f = ast.func
        args = [self.visit(a) for a in ast.args]
        if isinstance(f, BuiltinFunction):
            if f.op == 'index':
                m, i = self.location_getter.visit(ast)

                if i not in m:
                    t = ast.annotated_type.type_name
                    if isinstance(t, Mapping):
                        m[i] = {}
                    elif t == TypeName.uint_type():
                        m[i] = 0
                    else:
                        SimulationException(f'No default value for type {t}', ast)
                return m[i]
            elif f.op == 'parenthesis':
                return args[0]
            elif f.op == 'ite':
                if args[0]:
                    return args[1]
                else:
                    return args[2]
            elif f.op == '/':
                return args[0] // args[1]
            elif f.is_arithmetic() or f.is_comp():
                expr = f.format_string().format(*args)
                try:
                    r = eval(expr)
                except TypeError as e:
                    raise SimulationException(f'Could not compute {expr}', ast) from e
                return r
            elif f.op == '==':
                return args[0] == args[1]
            elif f.op == '!=':
                return args[0] != args[1]
            elif f.op == '&&':
                return args[0] and args[1]
            elif f.op == '||':
                return args[0] or args[1]
            elif f.op == '!':
                return not args[0]
            else:
                raise SimulationException(f'Unsupported operation {f.op}', ast)
        else:
            raise NotImplementedError('Function call')

    def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
        return ast.value

    def visitNumberLiteralExpr(self, ast: NumberLiteralExpr):
        return ast.value

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        m, i = self.location_getter.visit(ast)
        return m[i]

    def visitMeExpr(self, _: MeExpr):
        return self.me

    def visitAllExpr(self, _: AllExpr):
        return 'all'

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        return self.visit(ast.expr)

    def visitReturnStatement(self, ast: ReturnStatement):
        self.return_value = self.visit(ast.expr)

    def visitRequireStatement(self, ast: RequireStatement):
        cond = self.visit(ast.condition)
        if not cond:
            raise SimulationException(f'"require" condition does not hold in state {self.state}', ast)

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        m, i = self.location_getter.visit(ast.lhs)
        e = self.visit(ast.rhs)
        m[i] = e

    def visitBlock(self, ast: Block):
        for s in ast.statements:
            self.visit(s)
            if self.return_value:
                return self.return_value

    def visitTypeName(self, ast: TypeName):
        raise SimulationException('Should not evaluate types', ast)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        self.handle_declaration(ast.variable_declaration, ast.expr)

    def handle_function_definition(self, ast: ConstructorOrFunctionDefinition):
        for i, p in enumerate(ast.parameters):
            v = self.parameters[i]
            self.state[p] = v

            self.values[p] = v
            self.owners[p] = self.visit(p.annotated_type.privacy_annotation.privacy_annotation_label())

        r = self.visit(ast.body)

        # only keep state variables
        for k in set(self.state.keys()):
            if not isinstance(k, StateVariableDeclaration):
                del self.state[k]

        return r

    def visitFunctionDefinition(self, ast: FunctionDefinition):
        return self.handle_function_definition(ast)

    def handle_declaration(self, d: Union[VariableDeclaration, StateVariableDeclaration], expr: Expression):
        if expr:
            e = self.visit(expr)
            self.state[d] = e
        elif isinstance(d.annotated_type.type_name, Mapping):
            self.state[d] = {}
        else:
            self.state[d] = None

    def visitConstructorDefinition(self, ast: ConstructorDefinition):
        assert (isinstance(ast.parent, ContractDefinition))
        for d in ast.parent.state_variable_declarations:
            self.handle_declaration(d, d.expr)
        return self.handle_function_definition(ast)


class LocationGetter(AstVisitor):

    def __init__(self, s: Simulator):
        super().__init__(None)
        self.s = s

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        f = ast.func
        if isinstance(f, BuiltinFunction):
            if f.op == 'index':
                arr = self.s.visit(ast.args[0])
                index = self.s.visit(ast.args[1])
                return arr, index
        raise ValueError(ast)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        return self.s.state, ast.target


class SimulationException(Exception):

    def __init__(self, msg, ast: AST):
        super().__init__(f'{msg}\nFor: {str(ast)}')
