from zkay.type_check.contains_private import contains_private
from zkay.type_check.final_checker import check_final
from zkay.type_check.type_exceptions import TypeMismatchException, TypeException
from zkay.zkay_ast.ast import IdentifierExpr, ReturnStatement, IfStatement, \
    AssignmentExpr, BooleanLiteralExpr, NumberLiteralExpr, AnnotatedTypeName, Expression, TypeName, \
    FunctionDefinition, StateVariableDeclaration, Mapping, \
    AssignmentStatement, MeExpr, ConstructorDefinition, ReclassifyExpr, FunctionCallExpr, \
    BuiltinFunction, VariableDeclarationStatement, RequireStatement, MemberAccessExpr, TupleType, Identifier, IndexExpr, Array, \
    LocationExpr, CastExpr, NewExpr
from zkay.zkay_ast.visitor.visitor import AstVisitor


def type_check(ast):
    check_final(ast)
    v = TypeCheckVisitor()
    v.visit(ast)


class TypeCheckVisitor(AstVisitor):

    def get_rhs(self, rhs: Expression, expected_type: AnnotatedTypeName):
        instance = rhs.instanceof(expected_type)
        if not instance:
            raise TypeMismatchException(expected_type, rhs.annotated_type, rhs)
        elif instance == 'make-private':
            return self.make_private(rhs, expected_type.privacy_annotation)
        else:
            return rhs

    @staticmethod
    def check_for_invalid_private_type(ast):
        assert hasattr(ast, 'annotated_type')
        at = ast.annotated_type
        if at.is_private() and not at.type_name.can_be_private():
            raise TypeException(f"Type {at.type_name} cannot be private", ast.annotated_type)

    def visitAssignmentExpr(self, ast: AssignmentExpr):
        raise TypeException("Subexpressions with side-effects are currently not supported", ast)

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        # NB TODO? Should we optionally disallow writes to variables which are owned by someone else (with e.g. a new modifier)
        #if ast.lhs.annotated_type.is_private():
        #    expected_rhs_type = AnnotatedTypeName(ast.lhs.annotated_type.type_name, Expression.me_expr())
        #    if not ast.lhs.instanceof(expected_rhs_type):
        #        raise TypeException("Only owner can assign to its private variables", ast)

        if not isinstance(ast.lhs, LocationExpr):
            raise TypeException("Assignment target is not a location", ast.lhs)

        expected_type = ast.lhs.annotated_type
        ast.rhs = self.get_rhs(ast.rhs, expected_type)
        ast.annotated_type = expected_type

        # prevent modifying final
        if isinstance(ast, AssignmentExpr):
            f = ast.statement.function
        else:
            f = ast.function
        if isinstance(ast.lhs, IdentifierExpr):
            target = ast.lhs.target
            if hasattr(target, 'keywords'):
                if 'final' in target.keywords:
                    if isinstance(target, StateVariableDeclaration) and isinstance(f, ConstructorDefinition):
                        # assignment allowed
                        pass
                    else:
                        raise TypeException('Modifying "final" variable', ast)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        if ast.expr:
            ast.expr = self.get_rhs(ast.expr, ast.variable_declaration.annotated_type)

    def make_private_if_not_already(self, ast: Expression):
        if ast.annotated_type.is_private():
            expected = AnnotatedTypeName(ast.annotated_type.type_name, Expression.me_expr())
            if not ast.instanceof(expected):
                raise TypeMismatchException(expected, ast.annotated_type, ast)
            return ast
        else:
            return self.make_private(ast, Expression.me_expr())

    @staticmethod
    def has_private_type(ast: Expression):
        return ast.annotated_type.is_private()

    def handle_builtin_function_call(self, ast: FunctionCallExpr, func: BuiltinFunction):
        # handle special cases
        if func.is_ite():
            cond_t = ast.args[0].annotated_type

            # Ensure that condition is boolean
            if cond_t.type_name != TypeName.bool_type():
                raise TypeMismatchException(TypeName.bool_type(), cond_t.type_name, ast.args[0])

            # Check if both branches have the same data type
            t = ast.args[1].annotated_type.type_name
            if not ast.args[2].instanceof_data_type(t):
                raise TypeMismatchException(t, ast.args[2].annotated_type.type_name, ast.args[2])

            # Convert all args to private if one is private
            private_args = any(map(self.has_private_type, ast.args[1:]))
            if private_args or cond_t.is_private():
                ast.args[1:] = map(self.make_private_if_not_already, ast.args[1:])

            if cond_t.is_public():
                ast.annotated_type = AnnotatedTypeName(t, Expression.me_expr() if private_args else None)
            else:
                func.is_private = True
                ast.annotated_type = AnnotatedTypeName(t, Expression.me_expr())
            return
        elif func.is_parenthesis():
            ast.annotated_type = ast.args[0].annotated_type
            return
        elif func.is_neg_sign():
            raise TypeException('Unary negation is currently not supported (makes no sense for unsigned types)', ast)

        # Check data types
        parameter_types = func.input_types()
        if func.is_eq():
            parameter_types = 2 * [ast.args[0].annotated_type.type_name]
        for arg, t in zip(ast.args, parameter_types):
            if not arg.instanceof_data_type(t):
                raise TypeMismatchException(t, arg.annotated_type.type_name, arg)

        # Check privacy type and convert if necessary
        private_args = any(map(self.has_private_type, ast.args))
        if private_args:
            if func.can_be_private():
                func.is_private = True
                ast.args[:] = map(self.make_private_if_not_already, ast.args)
                ast.annotated_type = AnnotatedTypeName(func.output_type(), Expression.me_expr())
            else:
                raise TypeException(f'Operation \'{func.op}\' does not support private operands', ast)
        else:
            ast.annotated_type = AnnotatedTypeName(func.output_type())

    @staticmethod
    def is_accessible_by_invoker(ast: Expression):
        return True
        #return ast.annotated_type.is_public() or ast.is_lvalue() or \
        #       ast.instanceof(AnnotatedTypeName(ast.annotated_type.type_name, Expression.me_expr()))

    @staticmethod
    def make_private(expr: Expression, privacy: Expression):
        assert (privacy.privacy_annotation_label() is not None)

        pl = privacy.privacy_annotation_label().clone()
        if isinstance(pl, Identifier):
            pl = IdentifierExpr(pl, AnnotatedTypeName.address_all())
        r = ReclassifyExpr(expr, pl)

        # set type
        r.annotated_type = AnnotatedTypeName(expr.annotated_type.type_name, privacy)
        TypeCheckVisitor.check_for_invalid_private_type(r)

        # propagate side effects
        r.has_side_effects = expr.has_side_effects

        # set statement
        r.statement = expr.statement

        # set parents
        r.parent = expr.parent
        r.annotated_type.parent = r
        expr.parent = r

        return r

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            self.handle_builtin_function_call(ast, ast.func)
        elif isinstance(ast.func, LocationExpr):
            ft = ast.func.annotated_type.type_name

            if len(ft.parameters) != len(ast.args):
                raise TypeException("Wrong number of arguments", ast.func)

            # Check arguments
            for i in range(len(ast.args)):
                ast.args[i] = self.get_rhs(ast.args[i], ft.parameters[i].annotated_type)

            # Set expression type to return type
            if len(ft.return_parameters) == 1:
                ast.annotated_type = ft.return_parameters[0].annotated_type.clone()
            else:
                # TODO maybe not None label in the future
                ast.annotated_type = AnnotatedTypeName(TupleType([t.annotated_type for t in ft.return_parameters]), None)
        else:
            raise TypeException('Invalid function call', ast)

    def visitCastExpr(self, ast: CastExpr):
        ast.annotated_type = AnnotatedTypeName(ast.t, ast.args[0].annotated_type.privacy_annotation)

    def visitNewExpr(self, ast: NewExpr):
        # already has correct type
        pass

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        assert ast.target is not None
        ast.annotated_type = ast.target.annotated_type.clone()

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        if not ast.privacy.privacy_annotation_label():
            raise TypeException('Second argument of "reveal" cannot be used as a privacy type', ast)

        # NB prevent any redundant reveal (not just for public)
        ast.annotated_type = AnnotatedTypeName(ast.expr.annotated_type.type_name, ast.privacy)
        if ast.instanceof(ast.expr.annotated_type) is True:
            raise TypeException(f'Redundant "reveal": Expression is already "@{ast.privacy.code()}"', ast)
        self.check_for_invalid_private_type(ast)

    def visitIfStatement(self, ast: IfStatement):
        b = ast.condition
        expected = AnnotatedTypeName.bool_all()
        if not b.instanceof(expected):
            raise TypeMismatchException(expected, b.annotated_type, b)

    def visitReturnStatement(self, ast: ReturnStatement):
        assert (isinstance(ast.function, FunctionDefinition))
        expected_types = ast.function.get_return_type()

        if ast.expr is None and expected_types is not None:
            raise TypeMismatchException(expected_types, None, ast)
        elif ast.expr is not None:
            instance = ast.expr.instanceof(expected_types)
            if not instance:
                raise TypeMismatchException(expected_types, ast.expr.annotated_type, ast)
            elif instance == 'make-private':
                ast.expr = self.make_private(ast.expr, expected_types.privacy_annotation)

    def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
        ast.annotated_type = AnnotatedTypeName.bool_all()

    def visitNumberLiteralExpr(self, ast: NumberLiteralExpr):
        # Number literal does not include sign
        assert ast.value >= 0
        ast.annotated_type = AnnotatedTypeName.uint_all()

    def visitMeExpr(self, ast: MeExpr):
        ast.annotated_type = AnnotatedTypeName.address_all()

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if isinstance(ast.target, Mapping):
            # no action necessary, the identifier will be replaced later
            pass
        else:
            ast.annotated_type = ast.target.annotated_type.clone()

            if not self.is_accessible_by_invoker(ast):
                raise TypeException("Tried to read value which cannot be proven to be owned by the transaction invoker", ast)

    def visitIndexExpr(self, ast: IndexExpr):
        arr = ast.arr
        index = ast.key

        map_t = arr.annotated_type
        # should have already been checked
        assert (map_t.privacy_annotation.is_all_expr())

        # do actual type checking
        if isinstance(map_t.type_name, Mapping):
            key_type = map_t.type_name.key_type
            expected = AnnotatedTypeName(key_type, Expression.all_expr())
            instance = index.instanceof(expected)
            if not instance:
                raise TypeMismatchException(expected, index.annotated_type, ast)

            # record indexing information
            if map_t.type_name.key_label is not None: # TODO modification correct?
                if index.privacy_annotation_label():
                    map_t.type_name.instantiated_key = index
                else:
                    raise TypeException(f'Index cannot be used as a privacy type for array of type {map_t}', ast)

            # determine value type
            ast.annotated_type = map_t.type_name.value_type

            if not self.is_accessible_by_invoker(ast):
                raise TypeException("Tried to read value which cannot be proven to be owned by the transaction invoker", ast)
        elif isinstance(map_t.type_name, Array):
            if ast.key.annotated_type.is_private():
                raise TypeException('No private array index', ast)
            if not ast.key.instanceof_data_type(TypeName.uint_type()):
                raise TypeException('Array index must be numeric', ast)
            ast.annotated_type = map_t.type_name.value_type
        else:
            raise TypeException('Indexing into non-mapping', ast)

    def visitFunctionDefinition(self, ast: FunctionDefinition):
        for t in ast.get_parameter_types():
            ann = t.privacy_annotation
            if ann.is_all_expr() or ann.is_me_expr():
                continue
            else:
                raise TypeException(f'Only me/all accepted as privacy type of function parameters', ast)

    def visitStateVariableDeclaration(self, ast: StateVariableDeclaration):
        if ast.expr:
            # prevent private operations in declaration
            if contains_private(ast):
                raise TypeException('Private assignments to state variables must be in the constructor', ast)

            # check type
            self.get_rhs(ast.expr, ast.annotated_type)

        # prevent "me" annotation
        p = ast.annotated_type.privacy_annotation
        if p.is_me_expr():
            raise TypeException(f'State variables cannot be annotated as me', ast)

    def visitMapping(self, ast: Mapping):
        if ast.key_label is not None:
            if ast.key_type != TypeName.address_type():
                raise TypeException(f'Only addresses can be annotated', ast)

    def visitRequireStatement(self, ast: RequireStatement):
        if not ast.condition.annotated_type.privacy_annotation.is_all_expr():
            raise TypeException(f'require needs public argument', ast)

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
        if ast.privacy_annotation != Expression.all_expr():
            if not ast.type_name.can_be_private():
                raise TypeException(f'Currently, we do not support private {str(ast.type_name)}', ast)

        p = ast.privacy_annotation
        if isinstance(p, IdentifierExpr):
            t = p.target
            if isinstance(t, Mapping):
                # no action necessary, this is the case: mapping(address!x => uint@x)
                pass
            elif not t.is_final:
                raise TypeException('Privacy annotations must be "final", if they are expressions', ast)
            elif t.annotated_type != AnnotatedTypeName.address_all():
                raise TypeException(f'Privacy type is not a public address, but {str(t.annotated_type)}', ast)
