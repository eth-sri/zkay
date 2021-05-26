from zkay.type_check.contains_private import contains_private
from zkay.type_check.final_checker import check_final
from zkay.type_check.type_exceptions import TypeMismatchException, TypeException
from zkay.zkay_ast.ast import FunctionTypeName, IdentifierExpr, ReturnStatement, IfStatement, AnnotatedTypeName, \
    Expression, TypeName, \
    StateVariableDeclaration, Mapping, AssignmentStatement, MeExpr, ReclassifyExpr, FunctionCallExpr, \
    BuiltinFunction, VariableDeclarationStatement, RequireStatement, MemberAccessExpr, TupleType, IndexExpr, Array, \
    LocationExpr, NewExpr, TupleExpr, ConstructorOrFunctionDefinition, WhileStatement, ForStatement, NumberLiteralType, \
    BooleanLiteralType, EnumValue, EnumTypeName, EnumDefinition, EnumValueTypeName, PrimitiveCastExpr, \
    UserDefinedTypeName, get_privacy_expr_from_label, issue_compiler_warning, AllExpr, ContractDefinition, \
    RehomExpr
from zkay.zkay_ast.homomorphism import Homomorphism
from zkay.zkay_ast.visitor.deep_copy import replace_expr
from zkay.zkay_ast.visitor.visitor import AstVisitor


def type_check(ast):
    check_final(ast)
    v = TypeCheckVisitor()
    v.visit(ast)


class TypeCheckVisitor(AstVisitor):

    def get_rhs(self, rhs: Expression, expected_type: AnnotatedTypeName):
        if isinstance(rhs, TupleExpr):
            if not isinstance(rhs, TupleExpr) or not isinstance(expected_type.type_name, TupleType) or len(rhs.elements) != len(expected_type.type_name.types):
                raise TypeMismatchException(expected_type, rhs.annotated_type, rhs)
            exprs = [self.get_rhs(a, e) for e, a, in zip(expected_type.type_name.types, rhs.elements)]
            return replace_expr(rhs, TupleExpr(exprs)).as_type(TupleType([e.annotated_type for e in exprs]))

        require_rehom = False
        instance = rhs.instanceof(expected_type)

        if not instance:
            require_rehom = True
            expected_matching_hom = expected_type.with_homomorphism(rhs.annotated_type.homomorphism)
            instance = rhs.instanceof(expected_matching_hom)

        if not instance:
            raise TypeMismatchException(expected_type, rhs.annotated_type, rhs)
        else:
            if rhs.annotated_type.type_name != expected_type.type_name:
                rhs = self.implicitly_converted_to(rhs, expected_type.type_name)

            if instance == 'make-private':
                return self.make_private(rhs, expected_type.privacy_annotation, expected_type.homomorphism)
            elif require_rehom:
                return self.try_rehom(rhs, expected_type)
            else:
                return rhs

    @staticmethod
    def check_for_invalid_private_type(ast):
        assert hasattr(ast, 'annotated_type')
        at = ast.annotated_type
        if at.is_private() and not at.type_name.can_be_private():
            raise TypeException(f"Type {at.type_name} cannot be private", ast.annotated_type)

    def check_final(self, fct: ConstructorOrFunctionDefinition, ast: Expression):
        if isinstance(ast, IdentifierExpr):
            target = ast.target
            if hasattr(target, 'keywords'):
                if 'final' in target.keywords:
                    if isinstance(target, StateVariableDeclaration) and fct.is_constructor:
                        # assignment allowed
                        pass
                    else:
                        raise TypeException('Modifying "final" variable', ast)
        else:
            assert isinstance(ast, TupleExpr)
            for elem in ast.elements:
                self.check_final(fct, elem)

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        if not isinstance(ast.lhs, (TupleExpr, LocationExpr)):
            raise TypeException("Assignment target is not a location", ast.lhs)

        expected_type = ast.lhs.annotated_type
        ast.rhs = self.get_rhs(ast.rhs, expected_type)

        # prevent modifying final
        f = ast.function
        if isinstance(ast.lhs, (IdentifierExpr, TupleExpr)):
            self.check_final(f, ast.lhs)

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        if ast.expr:
            ast.expr = self.get_rhs(ast.expr, ast.variable_declaration.annotated_type)

    @staticmethod
    def has_private_type(ast: Expression):
        return ast.annotated_type.is_private()

    @staticmethod
    def has_literal_type(ast: Expression):
        return isinstance(ast.annotated_type.type_name, (NumberLiteralType, BooleanLiteralType))

    def handle_builtin_function_call(self, ast: FunctionCallExpr, func: BuiltinFunction):
        if func.is_parenthesis():
            ast.annotated_type = ast.args[0].annotated_type
            return

        all_args_all_or_me = all(map(lambda x: x.annotated_type.is_accessible(ast.analysis), ast.args))
        is_public_ite = func.is_ite() and ast.args[0].annotated_type.is_public()
        if all_args_all_or_me or is_public_ite:
            self.handle_unhom_builtin_function_call(ast, func)
        else:
            self.handle_homomorphic_builtin_function_call(ast, func)

    def handle_unhom_builtin_function_call(self, ast: FunctionCallExpr, func: BuiltinFunction):
        # handle special cases
        if func.is_ite():
            cond_t = ast.args[0].annotated_type

            # Ensure that condition is boolean
            if not cond_t.type_name.implicitly_convertible_to(TypeName.bool_type()):
                raise TypeMismatchException(TypeName.bool_type(), cond_t.type_name, ast.args[0])

            res_t = ast.args[1].annotated_type.type_name.combined_type(ast.args[2].annotated_type.type_name, True)

            if cond_t.is_private():
                # Everything is turned private
                func.is_private = True
                a = res_t.annotate(Expression.me_expr())
            else:
                hom = self.combine_homomorphism(ast.args[1], ast.args[2])
                true_type = ast.args[1].annotated_type.with_homomorphism(hom)
                false_type = ast.args[2].annotated_type.with_homomorphism(hom)
                p = true_type.combined_privacy(ast.analysis, false_type)
                a = res_t.annotate(p).with_homomorphism(hom)
            ast.args[1] = self.get_rhs(ast.args[1], a)
            ast.args[2] = self.get_rhs(ast.args[2], a)

            ast.annotated_type = a
            return

        # Check that argument types conform to op signature
        parameter_types = func.input_types()
        if not func.is_eq():
            for arg, t in zip(ast.args, parameter_types):
                if not arg.instanceof_data_type(t):
                    raise TypeMismatchException(t, arg.annotated_type.type_name, arg)

        t1 = ast.args[0].annotated_type.type_name
        t2 = None if len(ast.args) == 1 else ast.args[1].annotated_type.type_name

        if len(ast.args) == 1:
            arg_t = 'lit' if ast.args[0].annotated_type.type_name.is_literal else t1
        else:
            assert len(ast.args) == 2
            is_eq_with_tuples = func.is_eq() and isinstance(t1, TupleType)
            arg_t = t1.combined_type(t2, convert_literals=is_eq_with_tuples)

        # Infer argument and output types
        if arg_t == 'lit':
            res = func.op_func(*[arg.annotated_type.type_name.value for arg in ast.args])
            if isinstance(res, bool):
                assert func.output_type() == TypeName.bool_type()
                out_t = BooleanLiteralType(res)
            else:
                assert func.output_type() == TypeName.number_type()
                out_t = NumberLiteralType(res)
            if func.is_eq():
                arg_t = t1.to_abstract_type().combined_type(t2.to_abstract_type(), True)
        elif func.output_type() == TypeName.bool_type():
            out_t = TypeName.bool_type()
        else:
            out_t = arg_t

        assert arg_t is not None and (arg_t != 'lit' or not func.is_eq())

        private_args = any(map(self.has_private_type, ast.args))
        if private_args:
            assert arg_t != 'lit'
            if func.can_be_private():
                if func.is_shiftop():
                    if not ast.args[1].annotated_type.type_name.is_literal:
                        raise TypeException('Private shift expressions must use a constant (literal) shift amount', ast.args[1])
                    if ast.args[1].annotated_type.type_name.value < 0:
                        raise TypeException('Cannot shift by negative amount', ast.args[1])
                if func.is_bitop() or func.is_shiftop():
                    for arg in ast.args:
                        if arg.annotated_type.type_name.elem_bitwidth == 256:
                            raise TypeException('Private bitwise and shift operations are only supported for integer types < 256 bit, '
                                                'please use a smaller type', arg)

                if func.is_arithmetic():
                    for a in ast.args:
                        if a.annotated_type.type_name.elem_bitwidth == 256:
                            issue_compiler_warning(func, 'Possible field prime overflow',
                                                         'Private arithmetic 256bit operations overflow at FIELD_PRIME.\n'
                                                         'If you need correct overflow behavior, use a smaller integer type.')
                            break
                elif func.is_comp():
                    for a in ast.args:
                        if a.annotated_type.type_name.elem_bitwidth == 256:
                            issue_compiler_warning(func, 'Possible private comparison failure',
                                                         'Private 256bit comparison operations will fail for values >= 2^252.\n'
                                                         'If you cannot guarantee that the value stays in range, you must use '
                                                         'a smaller integer type to ensure correctness.')
                            break

                func.is_private = True
                p = Expression.me_expr()
            else:
                raise TypeException(f'Operation \'{func.op}\' does not support private operands', ast)
        else:
            p = None

        if arg_t != 'lit':
            # Add implicit casts for arguments
            arg_pt = arg_t.annotate(p)
            if func.is_shiftop() and p is not None:
                ast.args[0] = self.get_rhs(ast.args[0], arg_pt)
            else:
                ast.args[:] = map(lambda argument: self.get_rhs(argument, arg_pt), ast.args)

        ast.annotated_type = out_t.annotate(p)

    def handle_homomorphic_builtin_function_call(self, ast: FunctionCallExpr, func: BuiltinFunction):
        # First - same as non-homomorphic - check that argument types conform to op signature
        if not func.is_eq():
            for arg, t in zip(ast.args, func.input_types()):
                if not arg.instanceof_data_type(t):
                    raise TypeMismatchException(t, arg.annotated_type.type_name, arg)

        homomorphic_func = func.select_homomorphic_overload(ast.args, ast.analysis)
        if homomorphic_func is None:
            raise TypeException(f'Operation \'{func.op}\' requires all arguments to be accessible, '
                                f'i.e. @all or provably equal to @me', ast)

        # We could perform homomorphic operations on-chain by using some Solidity arbitrary precision math library.
        # For now, keep it simple and evaluate homomorphic operations in Python and check the result in the circuit.
        func.is_private = True

        ast.annotated_type = homomorphic_func.output_type()
        func.homomorphism = ast.annotated_type.homomorphism
        expected_arg_types = homomorphic_func.input_types()

        # Check that the argument types are correct
        ast.args[:] = map(lambda arg, arg_pt: self.get_rhs(arg, arg_pt),
                          ast.args, expected_arg_types)

    @staticmethod
    def is_accessible_by_invoker(ast: Expression):
        return True
        #return ast.annotated_type.is_public() or ast.is_lvalue() or \
        #       ast.instanceof(AnnotatedTypeName(ast.annotated_type.type_name, Expression.me_expr()))

    @staticmethod
    def combine_homomorphism(lhs: Expression, rhs: Expression) -> Homomorphism:
        if lhs.annotated_type.homomorphism == rhs.annotated_type.homomorphism:
            return lhs.annotated_type.homomorphism
        elif TypeCheckVisitor.can_rehom(lhs):
            return rhs.annotated_type.homomorphism
        else:
            return lhs.annotated_type.homomorphism

    @staticmethod
    def can_rehom(ast: Expression) -> bool:
        if ast.annotated_type.is_accessible(ast.analysis):
            return True
        if isinstance(ast, ReclassifyExpr):
            return True
        if isinstance(ast, PrimitiveCastExpr):
            return TypeCheckVisitor.can_rehom(ast.expr)
        if isinstance(ast, FunctionCallExpr) and isinstance(ast.func, BuiltinFunction) and ast.func.is_ite() \
                and ast.args[0].annotated_type.is_public():
            return TypeCheckVisitor.can_rehom(ast.args[1]) and TypeCheckVisitor.can_rehom(ast.args[2])

        return False

    @staticmethod
    def try_rehom(rhs: Expression, expected_type: AnnotatedTypeName):
        if rhs.annotated_type.is_public():
            raise ValueError('Cannot change the homomorphism of a public value')

        if rhs.annotated_type.is_private_at_me(rhs.analysis):
            # The value is @me, so we can just insert a ReclassifyExpr to change
            # the homomorphism of this value, just like we do for public values.
            return TypeCheckVisitor.make_rehom(rhs, expected_type)

        if isinstance(rhs, ReclassifyExpr) and not isinstance(rhs, RehomExpr):
            # rhs is a valid ReclassifyExpr, i.e. the argument is public or @me-private
            # To create an expression with the correct homomorphism,
            # just change the ReclassifyExpr's output homomorphism
            rhs.homomorphism = expected_type.homomorphism
        elif isinstance(rhs, PrimitiveCastExpr):
            # Ignore primitive cast & recurse
            rhs.expr = TypeCheckVisitor.try_rehom(rhs.expr, expected_type)
        elif isinstance(rhs, FunctionCallExpr) and isinstance(rhs.func, BuiltinFunction) and rhs.func.is_ite() \
                and rhs.args[0].annotated_type.is_public():
            # Argument is public_cond ? true_val : false_val. Try to rehom both true_val and false_val
            rhs.args[1] = TypeCheckVisitor.try_rehom(rhs.args[1], expected_type)
            rhs.args[2] = TypeCheckVisitor.try_rehom(rhs.args[2], expected_type)
        else:
            raise TypeMismatchException(expected_type, rhs.annotated_type, rhs)

        # Rehom worked without throwing, change annotated_type and return
        rhs.annotated_type = rhs.annotated_type.with_homomorphism(expected_type.homomorphism)
        return rhs

    @staticmethod
    def make_rehom(expr: Expression, expected_type: AnnotatedTypeName):
        assert (expected_type.privacy_annotation.privacy_annotation_label() is not None)
        assert (expr.annotated_type.is_private_at_me(expr.analysis))
        assert (expected_type.is_private_at_me(expr.analysis))

        r = RehomExpr(expr, expected_type.homomorphism)

        # set type
        pl = get_privacy_expr_from_label(expected_type.privacy_annotation.privacy_annotation_label())
        r.annotated_type = AnnotatedTypeName(expr.annotated_type.type_name, pl, expected_type.homomorphism)
        TypeCheckVisitor.check_for_invalid_private_type(r)

        # set statement, parents, location
        TypeCheckVisitor.assign_location(r, expr)

        return r

    @staticmethod
    def make_private(expr: Expression, privacy: Expression, homomorphism: Homomorphism):
        assert (privacy.privacy_annotation_label() is not None)

        pl = get_privacy_expr_from_label(privacy.privacy_annotation_label())
        r = ReclassifyExpr(expr, pl, homomorphism)

        # set type
        r.annotated_type = AnnotatedTypeName(expr.annotated_type.type_name, pl.clone(), homomorphism)
        TypeCheckVisitor.check_for_invalid_private_type(r)

        # set statement, parents, location
        TypeCheckVisitor.assign_location(r, expr)

        return r

    @staticmethod
    def assign_location(target: Expression, source: Expression):
        # set statement
        target.statement = source.statement

        # set parents
        target.parent = source.parent
        target.annotated_type.parent = target
        source.parent = target

        # set source location
        target.line = source.line
        target.column = source.column

    @staticmethod
    def implicitly_converted_to(expr: Expression, t: TypeName) -> Expression:
        if isinstance(expr, ReclassifyExpr) and not expr.privacy.is_all_expr():
            # Cast the argument of the ReclassifyExpr instead
            expr.expr = TypeCheckVisitor.implicitly_converted_to(expr.expr, t)
            expr.annotated_type.type_name = expr.expr.annotated_type.type_name
            return expr

        assert expr.annotated_type.type_name.is_primitive_type()
        cast = PrimitiveCastExpr(t.clone(), expr, is_implicit=True).override(
            parent=expr.parent, statement=expr.statement, line=expr.line, column=expr.column)
        cast.elem_type.parent = cast
        expr.parent = cast
        cast.annotated_type = AnnotatedTypeName(t.clone(),
                                                expr.annotated_type.privacy_annotation.clone(),
                                                expr.annotated_type.homomorphism).override(parent=cast)
        return cast

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            self.handle_builtin_function_call(ast, ast.func)
        elif ast.is_cast:
            if not isinstance(ast.func.target, EnumDefinition):
                raise NotImplementedError('User type casts only implemented for enums')
            ast.annotated_type = self.handle_cast(ast.args[0], ast.func.target.annotated_type.type_name)
        elif isinstance(ast.func, LocationExpr):
            ft = ast.func.annotated_type.type_name
            assert(isinstance(ft, FunctionTypeName))

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

    def visitPrimitiveCastExpr(self, ast: PrimitiveCastExpr):
        ast.annotated_type = self.handle_cast(ast.expr, ast.elem_type)

    def handle_cast(self, expr: Expression, t: TypeName) -> AnnotatedTypeName:
        # because of the fake solidity check we already know that the cast is possible -> don't have to check if cast possible
        if expr.annotated_type.is_private():
            expected = AnnotatedTypeName(expr.annotated_type.type_name, Expression.me_expr())
            if not expr.instanceof(expected):
                raise TypeMismatchException(expected, expr.annotated_type, expr)
            return AnnotatedTypeName(t.clone(), Expression.me_expr())
        else:
            return AnnotatedTypeName(t.clone())

    def visitNewExpr(self, ast: NewExpr):
        # already has correct type
        pass

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        assert ast.target is not None
        if ast.expr.annotated_type.is_address() and ast.expr.annotated_type.is_private():
            raise TypeException("Cannot access members of private address variable", ast)
        ast.annotated_type = ast.target.annotated_type.clone()

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        if not ast.privacy.privacy_annotation_label():
            raise TypeException('Second argument of "reveal" cannot be used as a privacy type', ast)

        homomorphism = ast.homomorphism or ast.expr.annotated_type.homomorphism
        assert(homomorphism is not None)

        # Prevent ReclassifyExpr to all with homomorphic type
        if ast.privacy.is_all_expr() and homomorphism != Homomorphism.NON_HOMOMORPHIC:
            # If the target privacy is all, we infer a target homomorphism of NON_HOMOMORPHIC
            ast.homomorphism = homomorphism = Homomorphism.NON_HOMOMORPHIC

        # Make sure the first argument to reveal / rehom is public or private provably equal to @me
        is_expr_at_all = ast.expr.annotated_type.is_public()
        is_expr_at_me = ast.expr.annotated_type.is_private_at_me(ast.analysis)
        if not is_expr_at_all and not is_expr_at_me:
            raise TypeException(f'First argument of "{ast.func_name()}" must be accessible,'
                                f'i.e. @all or provably equal to @me', ast)

        # Prevent unhom(public_value)
        if is_expr_at_all and isinstance(ast, RehomExpr) and ast.homomorphism == Homomorphism.NON_HOMOMORPHIC:
            raise TypeException(f'Cannot use "{ast.homomorphism.rehom_expr_name}" on a public value', ast)

        # NB prevent any redundant reveal (not just for public)
        ast.annotated_type = AnnotatedTypeName(ast.expr.annotated_type.type_name, ast.privacy, homomorphism)
        if ast.instanceof(ast.expr.annotated_type) is True:
            raise TypeException(f'Redundant "{ast.func_name()}": Expression is already '
                                f'"@{ast.privacy.code()}{homomorphism}"', ast)
        self.check_for_invalid_private_type(ast)

    def visitIfStatement(self, ast: IfStatement):
        b = ast.condition
        if not b.instanceof_data_type(TypeName.bool_type()):
            raise TypeMismatchException(TypeName.bool_type(), b.annotated_type.type_name, b)
        if ast.condition.annotated_type.is_private():
            expected = AnnotatedTypeName(TypeName.bool_type(), Expression.me_expr())
            if not b.instanceof(expected):
                raise TypeMismatchException(expected, b.annotated_type, b)

    def visitWhileStatement(self, ast: WhileStatement):
        if not ast.condition.instanceof(AnnotatedTypeName.bool_all()):
            raise TypeMismatchException(AnnotatedTypeName.bool_all(), ast.condition.annotated_type, ast.condition)
        # must also later check that body and condition do not contain private expressions

    def visitForStatement(self, ast: ForStatement):
        if not ast.condition.instanceof(AnnotatedTypeName.bool_all()):
            raise TypeMismatchException(AnnotatedTypeName.bool_all(), ast.condition.annotated_type, ast.condition)
        # must also later check that body, update and condition do not contain private expressions

    def visitReturnStatement(self, ast: ReturnStatement):
        assert ast.function.is_function
        rt = AnnotatedTypeName(ast.function.return_type)
        if ast.expr is None:
            self.get_rhs(TupleExpr([]), rt)
        elif not isinstance(ast.expr, TupleExpr):
            ast.expr = self.get_rhs(TupleExpr([ast.expr]), rt)
        else:
            ast.expr = self.get_rhs(ast.expr, rt)

    def visitTupleExpr(self, ast: TupleExpr):
        ast.annotated_type = AnnotatedTypeName(TupleType([elem.annotated_type.clone() for elem in ast.elements]))

    def visitMeExpr(self, ast: MeExpr):
        ast.annotated_type = AnnotatedTypeName.address_all()

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if isinstance(ast.target, Mapping):
            # no action necessary, the identifier will be replaced later
            pass
        else:
            target = ast.target
            if isinstance(target, ContractDefinition):
                raise TypeException(f'Unsupported use of contract type in expression', ast)
            ast.annotated_type = target.annotated_type.clone()

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
            if not ast.key.instanceof_data_type(TypeName.number_type()):
                raise TypeException('Array index must be numeric', ast)
            ast.annotated_type = map_t.type_name.value_type
        else:
            raise TypeException('Indexing into non-mapping', ast)

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        for t in ast.parameter_types:
            if not isinstance(t.privacy_annotation, (MeExpr, AllExpr)):
                raise TypeException('Only me/all accepted as privacy type of function parameters', ast)

        if ast.can_be_external:
            for t in ast.return_type:
                if not isinstance(t.privacy_annotation, (MeExpr, AllExpr)):
                    raise TypeException('Only me/all accepted as privacy type of return values for public functions', ast)

    def visitEnumDefinition(self, ast: EnumDefinition):
        ast.annotated_type = AnnotatedTypeName(EnumTypeName(ast.qualified_name).override(target=ast))

    def visitEnumValue(self, ast: EnumValue):
        ast.annotated_type = AnnotatedTypeName(EnumValueTypeName(ast.qualified_name).override(target=ast))

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
        if type(ast.type_name) == UserDefinedTypeName:
            if not isinstance(ast.type_name.target, EnumDefinition):
                raise TypeException('Unsupported use of user-defined type', ast.type_name)
            ast.type_name = ast.type_name.target.annotated_type.type_name.clone()

        if ast.privacy_annotation != Expression.all_expr():
            if not ast.type_name.can_be_private():
                raise TypeException(f'Currently, we do not support private {str(ast.type_name)}', ast)
            if ast.homomorphism != Homomorphism.NON_HOMOMORPHIC:
                # only support uint8, uint16, uint24, uint32 homomorphic data types
                if not ast.type_name.is_numeric:
                    raise TypeException(f'Homomorphic type not supported for {str(ast.type_name)}: Only numeric types supported', ast)
                elif ast.type_name.signed:
                    raise TypeException(f'Homomorphic type not supported for {str(ast.type_name)}: Only unsigned types supported', ast)
                elif ast.type_name.elem_bitwidth > 32:
                    raise TypeException(f'Homomorphic type not supported for {str(ast.type_name)}: Only up to 32-bit numeric types supported', ast)

        p = ast.privacy_annotation
        if isinstance(p, IdentifierExpr):
            t = p.target
            if isinstance(t, Mapping):
                # no action necessary, this is the case: mapping(address!x => uint@x)
                pass
            elif not t.is_final and not t.is_constant:
                raise TypeException('Privacy annotations must be "final" or "constant", if they are expressions', p)
            elif t.annotated_type != AnnotatedTypeName.address_all():
                raise TypeException(f'Privacy type is not a public address, but {str(t.annotated_type)}', p)
