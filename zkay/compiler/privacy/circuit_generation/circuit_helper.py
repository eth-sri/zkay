from collections import OrderedDict
from contextlib import contextmanager, nullcontext
from typing import List, Optional, Tuple, Callable, Union, ContextManager

from zkay.compiler.name_remapper import CircVarRemapper
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircuitStatement, CircEncConstraint, CircVarDecl, \
    CircEqConstraint, CircComment, CircIndentBlock, CircGuardModification, CircCall, CircSymmEncConstraint
from zkay.compiler.privacy.circuit_generation.name_factory import NameFactory
from zkay.config import cfg
from zkay.type_check.type_checker import TypeCheckVisitor
from zkay.zkay_ast.ast import Expression, IdentifierExpr, PrivacyLabelExpr, \
    LocationExpr, TypeName, AssignmentStatement, UserDefinedTypeName, ConstructorOrFunctionDefinition, Parameter, \
    HybridArgumentIdf, EncryptionExpression, FunctionCallExpr, Identifier, AnnotatedTypeName, HybridArgType, CircuitInputStatement, \
    CircuitComputationStatement, AllExpr, MeExpr, ReturnStatement, Block, MemberAccessExpr, NumberLiteralType, BooleanLiteralType, \
    Statement, StateVariableDeclaration, IfStatement, TupleExpr, VariableDeclaration, IndexExpr, get_privacy_expr_from_label, \
    ExpressionStatement, NumberLiteralExpr, VariableDeclarationStatement, EnterPrivateKeyStatement, KeyLiteralExpr
from zkay.zkay_ast.visitor.deep_copy import deep_copy
from zkay.zkay_ast.visitor.transformer_visitor import AstTransformerVisitor


class CircuitHelper:
    """
    This class is used to construct abstract proof circuits during contract transformation.

    Typically there is one instance of this class for every function which requires verification.
    """

    def __init__(self, fct: ConstructorOrFunctionDefinition,
                 static_owner_labels: List[PrivacyLabelExpr],
                 expr_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 circ_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 internal_circuit: Optional['CircuitHelper'] = None):
        """
        Create a new CircuitHelper instance

        :param fct: The function which is associated with this proof circuit
        :param static_owner_labels: A list of all static privacy labels for this contract
                                    (i.e. MeExpr + Identifiers of all final address state variables)
        :param expr_trafo_constructor: Constructor of ZkayExpressionTransformer (cyclic dependency)
        :param circ_trafo_constructor: Constructor fo ZkayCircuitTransformer (cyclic dependency)
        :param internal_circuit [Optional]: When creating the external wrapper function (see ZkayContractTransformer),
                                            this should point to the CircuitHelper of the corresponding internal function.
                                            This circuit will then be initialized with the internal circuits data.
        """

        super().__init__()

        self.fct = fct
        """Function and verification contract corresponding to this circuit"""

        self.verifier_contract_filename: Optional[str] = None
        self.verifier_contract_type: Optional[UserDefinedTypeName] = None
        self.has_return_var = False
        """Metadata set later by ZkayContractTransformer"""

        self._expr_trafo: AstTransformerVisitor = expr_trafo_constructor(self)
        self._circ_trafo: AstTransformerVisitor = circ_trafo_constructor(self)
        """Transformer visitors"""

        self._phi: List[CircuitStatement] = []
        """
        List of proof circuit statements (assertions and assignments)

        WARNING: Never assign to self._phi, always access it using the phi property and only mutate it
        """

        self._secret_input_name_factory = NameFactory('secret', arg_type=HybridArgType.PRIV_CIRCUIT_VAL)
        """Name factory for private circuit inputs"""

        self._circ_temp_name_factory = NameFactory('tmp', arg_type=HybridArgType.TMP_CIRCUIT_VAL)
        """Name factory for temporary internal circuit variables"""

        self._in_name_factory = NameFactory(cfg.zk_in_name, arg_type=HybridArgType.PUB_CIRCUIT_ARG)
        """Name factory for public circuit inputs"""

        self._out_name_factory = NameFactory(cfg.zk_out_name, arg_type=HybridArgType.PUB_CIRCUIT_ARG)
        """Name factory for public circuit outputs"""

        # For a given owner label (idf or me), stores the corresponding assignment of the requested key to the corresponding in variable
        self._static_owner_labels = static_owner_labels
        """List of all statically known privacy labels for the contract of which this circuit is part of"""

        self._need_secret_key: bool = False
        """Whether msg.sender's secret key must be added to the private circuit inputs"""

        self._global_keys: OrderedDict[Union[MeExpr, Identifier], None] = OrderedDict([])
        """Set of statically known privacy labels (OrderedDict is used to ensure deterministic iteration order)"""

        self.function_calls_with_verification: List[FunctionCallExpr] = []
        """
        List of all (non-transitive) calls in self.fct's body to functions which require verification, in AST visiting order
        This is internally used to compute transitive in/out/privin sizes, but may also be useful when implementing a new
        circuit generator backend.
        """

        self.transitively_called_functions: OrderedDict[ConstructorOrFunctionDefinition, None] = None
        """Set (with deterministic order) of all functions which this circuit transitively calls."""

        if internal_circuit:
            # Inherit metadata from internal function's circuit helper
            self.verifier_contract_filename = internal_circuit.verifier_contract_filename
            internal_circuit.verifier_contract_filename = None
            self.verifier_contract_type = internal_circuit.verifier_contract_type
            internal_circuit.verifier_contract_type = None
            self._global_keys = internal_circuit._global_keys

            self.trans_priv_size = internal_circuit.priv_in_size_trans
            self.trans_in_size = internal_circuit.in_size_trans
            self.trans_out_size = internal_circuit.out_size_trans

            self._need_secret_key = internal_circuit._need_secret_key

            if internal_circuit.fct.requires_verification:
                self.transitively_called_functions = internal_circuit.transitively_called_functions.copy()
                self.transitively_called_functions[internal_circuit.fct] = None
            else:
                assert internal_circuit.transitively_called_functions is None
                self.transitively_called_functions = OrderedDict()
        else:
            # Set later by transform_internal_calls
            self.trans_priv_size, self.trans_in_size, self.trans_out_size = None, None, None

        self._remapper = CircVarRemapper()
        """Remapper instance used for SSA simulation"""

    def register_verification_contract_metadata(self, contract_type: TypeName, import_filename: str):
        self.verifier_contract_type = contract_type
        self.verifier_contract_filename = import_filename

    # Properties #

    def get_verification_contract_name(self) -> str:
        assert self.verifier_contract_type is not None
        return self.verifier_contract_type.code()

    def requires_zk_data_struct(self) -> bool:
        """
        Return true if a struct needs to be created in the solidity code to store public data (IO) associated with this circuit.

        A struct is used instead of plain temporary variables to bypass solidity's stack limit.
        """
        return self.out_size + self.in_size > 0

    @property
    def zk_data_struct_name(self):
        """Name of the data struct type"""
        return f'{cfg.zk_struct_prefix}_{self.fct.name}'

    @property
    def priv_in_size_trans(self) -> int:
        """Total size of all private inputs for this circuit (in # uints)"""
        return self.priv_in_size + self.trans_priv_size

    @property
    def priv_in_size(self) -> int:
        """Size of all private inputs required for self.fct only (without called functions, in #uints)"""
        return self._secret_input_name_factory.size

    @property
    def out_size_trans(self) -> int:
        """Total size of all public outputs for this circuit (in # uints)"""
        return self.out_size + self.trans_out_size

    @property
    def out_size(self) -> int:
        """Size of all public outputs required for self.fct only (without called functions, in #uints)"""
        return self._out_name_factory.size

    @property
    def in_size_trans(self) -> int:
        """Total size of all public inputs for this circuit (in # uints)"""
        return self.in_size + self.trans_in_size

    @property
    def in_size(self) -> int:
        """Size of all public inputs required for self.fct only (without called functions, in #uints)"""
        return self._in_name_factory.size

    @property
    def output_idfs(self) -> List[HybridArgumentIdf]:
        """All public output HybridArgumentIdfs (for self.fct only, w/o called functions)"""
        return self._out_name_factory.idfs

    @property
    def input_idfs(self) -> List[HybridArgumentIdf]:
        """All public input HybridArgumentIdfs (for self.fct only, w/o called functions)"""
        return self._in_name_factory.idfs

    @property
    def sec_idfs(self) -> List[HybridArgumentIdf]:
        """All private input HybridArgumentIdfs (for self.fct only, w/o called functions)"""
        return self._secret_input_name_factory.idfs

    @property
    def phi(self) -> List[CircuitStatement]:
        """List of abstract circuit statements which defines circuit semantics"""
        return self._phi

    @property
    def requested_global_keys(self) -> 'OrderedDict[Union[MeExpr, Identifier], None]':
        """Statically known keys required by this circuit"""
        return self._global_keys

    @property
    def public_arg_arrays(self) -> List[Tuple[str, int]]:
        """Returns names and lengths of all public parameter uint256 arrays which go into the verifier"""
        return [(self._in_name_factory.base_name, self.in_size_trans), (self._out_name_factory.base_name, self.out_size_trans)]

    @contextmanager
    def circ_indent_block(self, name: str = ''):
        """
        Return context manager which manages the lifetime of a CircIndentBlock.

        All statements which are inserted into self.phi during the lifetime of this context manager are automatically wrapped inside
        a CircIndentBlock statement with the supplied name.
        """
        old_len = len(self.phi)
        yield
        self.phi[:] = self.phi[:old_len] + [CircIndentBlock(name, self.phi[old_len:])]

    def guarded(self, guard_idf: HybridArgumentIdf, is_true: bool) -> ContextManager:
        """Return a context manager which manages the lifetime of a guard variable."""
        return CircGuardModification.guarded(self.phi, guard_idf, is_true)

    @staticmethod
    def get_glob_key_name(label: PrivacyLabelExpr) -> str:
        """Return the name of the HybridArgumentIdf which holds the statically known public key for the given privacy label."""
        assert isinstance(label, (MeExpr, Identifier))
        return f'glob_key_{label.name}'

    @staticmethod
    def get_own_secret_key_name() -> str:
        return f'glob_sk_me'

    def requires_verification(self) -> bool:
        """ Returns true if the function corresponding to this circuit requires a zk proof verification for correctness """
        req = self.in_size_trans > 0 or self.out_size_trans > 0 or self.priv_in_size_trans > 0
        assert req == self.fct.requires_verification
        return req

    # Solidity-side interface #

    def ensure_parameter_encryption(self, insert_loc_stmt: Statement, param: Parameter):
        """
        Make circuit prove that the encryption of the specified parameter is correct.
        """
        assert param.annotated_type.is_cipher()

        plain_idf = self._secret_input_name_factory.add_idf(param.idf.name, param.annotated_type.zkay_type.type_name)
        name = f'{self._in_name_factory.get_new_name(param.annotated_type.type_name)}_{param.idf.name}'
        cipher_idf = self._in_name_factory.add_idf(name, param.annotated_type.type_name)
        self._ensure_encryption(insert_loc_stmt, plain_idf, Expression.me_expr(), cipher_idf, True, False)

    def evaluate_expr_in_circuit(self, expr: Expression, new_privacy: PrivacyLabelExpr) -> LocationExpr:
        """
        Evaluate private expression and return result as a fresh out variable.

        Roughly corresponds to out() from paper

        Note: This function has side effects on expr.statement (adds a pre_statement)

        :param expr: [SIDE EFFECT] The expression which should be evaluated privately
        :param new_privacy: The circuit output should be encrypted for this owner (or plain if 'all')
        :return: Location expression which references the encrypted circuit result
        """
        with self.circ_indent_block(expr.code()):
            return self._get_circuit_output_for_private_expression(expr, new_privacy)

    def evaluate_stmt_in_circuit(self, ast: Statement) -> AssignmentStatement:
        """
        Evaluate an entire statement privately.

        This works by turning the statement into an assignment statement where the

        * lhs is a tuple of all external locations (defined outside statement), which are modified inside the statement
        * rhs is the return value of an inlined function call expression to a virtual function where body = the statement + return statement \
          which returns a tuple of the most recent SSA version of all modified locations

        Note: Modifying external locations which are not owned by @me inside the statement is illegal (would leak information).
        Note: At the moment, this is only used for if statements with a private condition.

        :param ast: the statement to evaluate inside the circuit
        :return: AssignmentStatement as described above
        """
        astmt = ExpressionStatement(NumberLiteralExpr(0))
        for var in ast.modified_values:
            if var.in_scope_at(ast):
                astmt = AssignmentStatement(None, None)
                break

        astmt.before_analysis = ast.before_analysis

        # External values written inside statement -> function return values
        ret_params = []
        for var in ast.modified_values:
            if var.in_scope_at(ast):
                # side effect affects location outside statement and has privacy @me
                assert ast.before_analysis.same_partition(var.privacy, Expression.me_expr())
                assert isinstance(var.target, (Parameter, VariableDeclaration, StateVariableDeclaration))
                t = var.target.annotated_type.zkay_type.type_name
                if not t.is_primitive_type():
                    raise NotImplementedError('Reference types inside private if statements are not supported')
                ret_param = IdentifierExpr(var.target.idf.clone(), AnnotatedTypeName(t, Expression.me_expr())).override(target=var.target)
                ret_param.statement = astmt
                ret_params.append(ret_param)

        # Build the imaginary function
        fdef = ConstructorOrFunctionDefinition(
            Identifier('<stmt_fct>'), [], ['private'],
            [Parameter([], ret.annotated_type, ret.target.idf) for ret in ret_params],
            Block([ast, ReturnStatement(TupleExpr(ret_params))])
        )
        fdef.original_body = fdef.body
        fdef.body.parent = fdef
        fdef.parent = ast

        # inline "Call" to the imaginary function
        fcall = FunctionCallExpr(IdentifierExpr('<stmt_fct>').override(target=fdef), [])
        fcall.statement = astmt
        ret_args = self.inline_function_call_into_circuit(fcall)

        # Move all return values out of the circuit
        if not isinstance(ret_args, TupleExpr):
            ret_args = TupleExpr([ret_args])
        for ret_arg in ret_args.elements:
            ret_arg.statement = astmt
        ret_arg_outs = [
            self._get_circuit_output_for_private_expression(ret_arg, Expression.me_expr())
            for ret_param, ret_arg in zip(ret_params, ret_args.elements)
        ]

        # Create assignment statement
        if ret_params:
            astmt.lhs = TupleExpr([ret_param.clone() for ret_param in ret_params])
            astmt.rhs = TupleExpr(ret_arg_outs)
            return astmt
        else:
            assert isinstance(astmt, ExpressionStatement)
            return astmt

    def invalidate_idf(self, target_idf: Identifier):
        if self._remapper.is_remapped(target_idf):
            self._remapper.reset_key(target_idf)

    def call_function(self, ast: FunctionCallExpr):
        """
        Include public function call to a function which requires verification in this circuit.

        :param ast: The function call to include, target function must require verification
        """
        assert ast.func.target.requires_verification
        self.function_calls_with_verification.append(ast)
        self.phi.append(CircCall(ast.func.target))

    def request_public_key(self, plabel: Union[MeExpr, Identifier], name):
        """
        Request key for the address corresponding to plabel from pki infrastructure and add it to the public circuit inputs.

        :param plabel: privacy label for which to request key
        :param name: name to use for the HybridArgumentIdf holding the key
        :return: HybridArgumentIdf containing the requested key and an AssignmentStatement which assigns the key request to the idf location
        """
        idf = self._in_name_factory.add_idf(name, TypeName.key_type())
        pki = IdentifierExpr(cfg.get_contract_var_name(cfg.pki_contract_name))
        privacy_label_expr = get_privacy_expr_from_label(plabel)
        return idf, idf.get_loc_expr().assign(pki.call('getPk', [self._expr_trafo.visit(privacy_label_expr)]))

    def request_private_key(self) -> List[Statement]:
        assert self._need_secret_key or any(p.annotated_type.is_cipher() for p in self.fct.parameters)
        self._secret_input_name_factory.add_idf(self.get_own_secret_key_name(), TypeName.key_type())
        return [EnterPrivateKeyStatement()]

    # Circuit-side interface #

    def add_to_circuit_inputs(self, expr: Expression) -> HybridArgumentIdf:
        """
        Add the provided expression to the public circuit inputs.

        Roughly corresponds to in() from paper

        If expr is encrypted (privacy != @all), this function also automatically ensures that the circuit has access to
        the correctly decrypted expression value in the form of a new private circuit input.

        If expr is an IdentifierExpr, its value will be cached
        (i.e. when the same identifier is needed again as a circuit input, its value will be retrieved from cache rather \
         than adding an expensive redundant input. The cache is invalidated as soon as the identifier is overwritten in public code)

        Note: This function has side effects on expr.statement (adds a pre_statement)

        :param expr: [SIDE EFFECT] expression which should be made available inside the circuit as an argument
        :return: HybridArgumentIdf which references the plaintext value of the newly added input
        """
        privacy = Expression.me_expr() if expr.annotated_type.is_private() else Expression.all_expr()

        expr_text = expr.code()
        input_expr = self._expr_trafo.visit(expr)
        t = input_expr.annotated_type.type_name

        # If expression has literal type -> evaluate it inside the circuit (constant folding will be used)
        # rather than introducing an unnecessary public circuit input (expensive)
        if isinstance(t, BooleanLiteralType):
            return self._evaluate_private_expression(input_expr, str(t.value))
        elif isinstance(t, NumberLiteralType):
            return self._evaluate_private_expression(input_expr, str(t.value))

        t_suffix = ''
        if isinstance(expr, IdentifierExpr):
            # Look in cache before doing expensive move-in
            if self._remapper.is_remapped(expr.target.idf):
                remapped_idf = self._remapper.get_current(expr.target.idf)
                return remapped_idf

            t_suffix = f'_{expr.idf.name}'

        # Generate circuit inputs
        if privacy.is_all_expr():
            tname = f'{self._in_name_factory.get_new_name(expr.annotated_type.type_name)}{t_suffix}'
            input_idf = self._in_name_factory.add_idf(tname, expr.annotated_type.type_name)
            self._phi.append(CircComment(f'{input_idf.name} = {expr_text}'))
            locally_decrypted_idf = input_idf
        else:
            # Encrypted inputs need to be decrypted inside the circuit (i.e. add plain as private input and prove encryption)
            tname = f'{self._secret_input_name_factory.get_new_name(expr.annotated_type.type_name)}{t_suffix}'
            locally_decrypted_idf = self._secret_input_name_factory.add_idf(tname, expr.annotated_type.type_name)
            cipher_t = TypeName.cipher_type(input_expr.annotated_type)
            tname = f'{self._in_name_factory.get_new_name(cipher_t)}{t_suffix}'
            input_idf = self._in_name_factory.add_idf(tname, cipher_t, IdentifierExpr(locally_decrypted_idf))

        # Add a CircuitInputStatement to the solidity code, which looks like a normal assignment statement,
        # but also signals the offchain simulator to perform decryption if necessary
        expr.statement.pre_statements.append(CircuitInputStatement(input_idf.get_loc_expr(), input_expr))

        if not privacy.is_all_expr():
            # Check if the secret plain input corresponds to the decrypted cipher value
            self._phi.append(CircComment(f'{locally_decrypted_idf} = dec({expr_text}) [{input_idf.name}]'))
            self._ensure_encryption(expr.statement, locally_decrypted_idf, Expression.me_expr(), input_idf, False, True)

        # Cache circuit input for later reuse if possible
        if cfg.opt_cache_circuit_inputs and isinstance(expr, IdentifierExpr):
            assert expr.annotated_type.type_name.is_primitive_type()
            self._remapper.remap(expr.target.idf, locally_decrypted_idf)

        return locally_decrypted_idf

    def get_remapped_idf_expr(self, idf: IdentifierExpr) -> LocationExpr:
        """
        Get location expression for the most recently assigned value of idf according to the SSA simulation.

        :param idf: Identifier expression to lookup
        :return: Either idf itself (not currently remapped)
                 or a loc expr for the HybridArgumentIdf which references the most recent value of idf
        """
        assert idf.target is not None
        assert not isinstance(idf.idf, HybridArgumentIdf)
        if self._remapper.is_remapped(idf.target.idf):
            remapped_idf = self._remapper.get_current(idf.target.idf)
            return remapped_idf.get_idf_expr(idf.parent).as_type(idf.annotated_type)
        else:
            return idf

    def create_new_idf_version_from_value(self, orig_idf: Identifier, expr: Expression):
        """
        Store expr in a new version of orig_idf (for SSA).

        :param orig_idf: the identifier which should be updated with a new value
        :param expr: the updated value
        :param is_local: whether orig_idf refers to a local variable (as opposed to a state variable)
        """
        tmp_var = self._create_temp_var(orig_idf.name, expr)
        self._remapper.remap(orig_idf, tmp_var)

    def inline_function_call_into_circuit(self, fcall: FunctionCallExpr) -> Union[Expression, TupleExpr]:
        """
        Inline an entire function call into the current circuit.

        :param fcall: Function call to inline
        :return: Expression (1 retval) / TupleExpr (multiple retvals) with return value(s)
        """
        assert isinstance(fcall.func, LocationExpr) and fcall.func.target is not None
        fdef = fcall.func.target
        with self._remapper.remap_scope(fcall.func.target.body):
            with nullcontext() if fcall.func.target.idf.name == '<stmt_fct>' else self.circ_indent_block(f'INLINED {fcall.code()}'):
                # Assign all arguments to temporary circuit variables which are designated as the current version of the parameter idfs
                for param, arg in zip(fdef.parameters, fcall.args):
                    self.phi.append(CircComment(f'ARG {param.idf.name}: {arg.code()}'))
                    with self.circ_indent_block():
                        self.create_new_idf_version_from_value(param.idf, arg)

                # Visit the untransformed target function body to include all statements in this circuit
                inlined_body = deep_copy(fdef.original_body, with_types=True, with_analysis=True)
                self._circ_trafo.visit(inlined_body)
                fcall.statement.pre_statements += inlined_body.pre_statements

                # Create TupleExpr with location expressions corresponding to the function return values as elements
                ret_idfs = [self._remapper.get_current(vd.idf) for vd in fdef.return_var_decls]
                ret = TupleExpr([IdentifierExpr(idf.clone()).as_type(idf.t) for idf in ret_idfs])
        if len(ret.elements) == 1:
            # Unpack 1-length tuple
            ret = ret.elements[0]
        return ret

    def add_assignment_to_circuit(self, ast: AssignmentStatement):
        """Include private assignment statement in this circuit."""
        self.phi.append(CircComment(ast.code()))
        self._add_assign(ast.lhs, ast.rhs)

    def add_var_decl_to_circuit(self, ast: VariableDeclarationStatement):
        self.phi.append(CircComment(ast.code()))
        if ast.expr is None:
            # Default initialization is made explicit for circuit variables
            t = ast.variable_declaration.annotated_type.type_name
            assert t.can_be_private()
            ast.expr = TypeCheckVisitor.implicitly_converted_to(NumberLiteralExpr(0).override(parent=ast, statement=ast), t.clone())
        self.create_new_idf_version_from_value(ast.variable_declaration.idf, ast.expr)

    def add_return_stmt_to_circuit(self, ast: ReturnStatement):
        self.phi.append(CircComment(ast.code()))
        assert ast.expr is not None
        if not isinstance(ast.expr, TupleExpr):
            ast.expr = TupleExpr([ast.expr])

        for vd, expr in zip(ast.function.return_var_decls, ast.expr.elements):
            # Assign return value to new version of return variable
            self.create_new_idf_version_from_value(vd.idf, expr)

    def add_if_statement_to_circuit(self, ast: IfStatement):
        """Include private if statement in this circuit."""

        # Handle if branch
        with self._remapper.remap_scope():
            comment = CircComment(f'if ({ast.condition.code()})')
            self._phi.append(comment)
            cond = self._evaluate_private_expression(ast.condition)
            comment.text += f' [{cond.name}]'
            self._circ_trafo.visitBlock(ast.then_branch, cond, True)
            then_remap = self._remapper.get_state()

            # Bubble up nested pre statements
            ast.pre_statements += ast.then_branch.pre_statements
            ast.then_branch.pre_statements = []

        # Handle else branch
        if ast.else_branch is not None:
            self._phi.append(CircComment(f'else [{cond.name}]'))
            self._circ_trafo.visitBlock(ast.else_branch, cond, False)

            # Bubble up nested pre statements
            ast.pre_statements += ast.else_branch.pre_statements
            ast.else_branch.pre_statements = []

        # SSA join branches (if both branches write to same external value -> cond assignment to select correct version)
        with self.circ_indent_block(f'JOIN [{cond.name}]'):
            cond_idf_expr = cond.get_idf_expr(ast)
            assert isinstance(cond_idf_expr, IdentifierExpr)
            self._remapper.join_branch(ast, cond_idf_expr, then_remap, self._create_temp_var)

    def add_block_to_circuit(self, ast: Block, guard_cond: Optional[HybridArgumentIdf], guard_val: Optional[bool]):
        assert ast.parent is not None
        is_already_scoped = isinstance(ast.parent, (ConstructorOrFunctionDefinition, IfStatement))
        self.phi.append(CircComment('{'))
        with self.circ_indent_block():
            with nullcontext() if guard_cond is None else self.guarded(guard_cond, guard_val):
                with nullcontext() if is_already_scoped else self._remapper.remap_scope(ast):
                    for stmt in ast.statements:
                        self._circ_trafo.visit(stmt)
                        # Bubble up nested pre statements
                        ast.pre_statements += stmt.pre_statements
                        stmt.pre_statements = []
        self.phi.append(CircComment('}'))

    # Internal functionality #

    def _get_canonical_privacy_label(self, analysis, privacy: PrivacyLabelExpr):
        """
        If privacy is equivalent to a static privacy label -> Return the corresponding static label, otherwise itself.

        :param analysis: analysis state at the statement where expression with the given privacy occurs
        :param privacy: original privacy label
        """
        for owner in self._static_owner_labels:
            if analysis.same_partition(owner, privacy):
                return owner
        return privacy

    def _create_temp_var(self, tag: str, expr: Expression) -> HybridArgumentIdf:
        """Assign expression to a fresh temporary circuit variable."""
        return self._evaluate_private_expression(expr, tmp_idf_suffix=f'_{tag}')

    def _add_assign(self, lhs: Expression, rhs: Expression):
        """
        Simulate an assignment of rhs to lhs inside the circuit.

        :param lhs: destination
        :param rhs: source
        """
        if isinstance(lhs, IdentifierExpr): # for now no ref types
            assert lhs.target is not None
            self.create_new_idf_version_from_value(lhs.target.idf, rhs)
        elif isinstance(lhs, IndexExpr):
            raise NotImplementedError()
        else:
            assert isinstance(lhs, TupleExpr)
            if isinstance(rhs, FunctionCallExpr):
                rhs = self._circ_trafo.visit(rhs)
            assert isinstance(rhs, TupleExpr) and len(lhs.elements) == len(rhs.elements)
            for e_l, e_r in zip(lhs.elements, rhs.elements):
                self._add_assign(e_l, e_r)

    def _get_circuit_output_for_private_expression(self, expr: Expression, new_privacy: PrivacyLabelExpr) -> LocationExpr:
        """
        Add evaluation of expr to the circuit and return the output HybridArgumentIdf corresponding to the evaluation result.

        Note: has side effects on expr.statement (adds pre_statement)

        :param expr: [SIDE EFFECT] expression to evaluate
        :param new_privacy: result owner (determines encryption key)
        :return: HybridArgumentIdf which references the circuit output containing the result of expr
        """
        is_circ_val = isinstance(expr, IdentifierExpr) and isinstance(expr.idf, HybridArgumentIdf) and expr.idf.arg_type != HybridArgType.PUB_CONTRACT_VAL
        if is_circ_val or expr.annotated_type.is_private() or expr.evaluate_privately:
            plain_result_idf = self._evaluate_private_expression(expr)
        else:
            # For public expressions which should not be evaluated in private, only the result is moved into the circuit
            plain_result_idf = self.add_to_circuit_inputs(expr)
        private_expr = plain_result_idf.get_idf_expr()

        t_suffix = ''
        if isinstance(expr, IdentifierExpr) and not is_circ_val:
            t_suffix += f'_{expr.idf.name}'

        if isinstance(new_privacy, AllExpr):
            # If the result is public, add an equality constraint to ensure that the user supplied public output
            # is equal to the circuit evaluation result
            tname = f'{self._out_name_factory.get_new_name(expr.annotated_type.type_name)}{t_suffix}'
            new_out_param = self._out_name_factory.add_idf(tname, expr.annotated_type.type_name, private_expr)
            self._phi.append(CircEqConstraint(plain_result_idf, new_out_param))
            out_var = new_out_param.get_loc_expr().explicitly_converted(expr.annotated_type.type_name)
        else:
            # If the result is encrypted, add an encryption constraint to ensure that the user supplied encrypted output
            # is equal to the correctly encrypted circuit evaluation result
            new_privacy = self._get_canonical_privacy_label(expr.analysis, new_privacy)
            privacy_label_expr = get_privacy_expr_from_label(new_privacy)
            cipher_t = TypeName.cipher_type(expr.annotated_type)
            tname = f'{self._out_name_factory.get_new_name(cipher_t)}{t_suffix}'
            new_out_param = self._out_name_factory.add_idf(tname, cipher_t, EncryptionExpression(private_expr, privacy_label_expr))
            self._ensure_encryption(expr.statement, plain_result_idf, new_privacy, new_out_param, False, False)
            out_var = new_out_param.get_loc_expr()

        # Add an invisible CircuitComputationStatement to the solidity code, which signals the offchain simulator,
        # that the value the contained out variable must be computed at this point by simulating expression evaluation
        expr.statement.pre_statements.append(CircuitComputationStatement(new_out_param))
        return out_var

    def _evaluate_private_expression(self, expr: Expression, tmp_idf_suffix='') -> HybridArgumentIdf:
        """
        Evaluate expr in the circuit (if not already done) and store result in a new temporary circuit variable.

        :param expr: expression to evaluate
        :param tmp_idf_suffix: name suffix for the new temporary circuit variable
        :return: temporary circuit variable HybridArgumentIdf which refers to the transformed circuit expression
        """
        assert not (isinstance(expr, MemberAccessExpr) and isinstance(expr.member, HybridArgumentIdf))
        if isinstance(expr, IdentifierExpr) and isinstance(expr.idf, HybridArgumentIdf) \
                and expr.idf.arg_type != HybridArgType.PUB_CONTRACT_VAL:
            # Already evaluated in circuit
            return expr.idf.clone()

        priv_expr = self._circ_trafo.visit(expr)
        tname = f'{self._circ_temp_name_factory.get_new_name(expr.annotated_type.type_name)}{tmp_idf_suffix}'
        tmp_circ_var_idf = self._circ_temp_name_factory.add_idf(tname, expr.annotated_type.type_name, priv_expr)
        stmt = CircVarDecl(tmp_circ_var_idf, priv_expr)
        self.phi.append(stmt)
        return tmp_circ_var_idf

    def _ensure_encryption(self, stmt: Statement, plain: HybridArgumentIdf, new_privacy: PrivacyLabelExpr,
                           cipher: HybridArgumentIdf, is_param: bool, is_dec: bool):
        """
        Make sure that cipher = enc(plain, getPk(new_privacy), priv_user_provided_rnd).

        This automatically requests necessary keys and adds a circuit input for the randomness.

        Note: This function adds pre-statements to stmt

        :param stmt [SIDE EFFECT]: the statement which contains the expression which requires this encryption
        :param plain: circuit variable referencing the plaintext value
        :param new_privacy: privacy label corresponding to the destination key address
        :param cipher: circuit variable referencing the encrypted value
        :param is_param: whether cipher is a function parameter
        :param is_dec: whether this is a decryption operation (user supplied plain) as opposed to an encryption operation (user supplied cipher)
        """
        if cfg.is_symmetric_cipher():
            # Need a different set of keys for hybrid-encryption (ecdh-based) backends
            self._require_secret_key()
            my_pk = self._require_public_key_for_label_at(stmt, Expression.me_expr())
            if is_dec:
                other_pk = self._get_public_key_in_sender_field(stmt, cipher)
            else:
                if new_privacy == Expression.me_expr():
                    other_pk = my_pk
                else:
                    other_pk = self._require_public_key_for_label_at(stmt, new_privacy)

                self.phi.append(CircComment(f'{cipher.name} = enc({plain.name}, ecdh({other_pk.name}, my_sk))'))
            self._phi.append(CircSymmEncConstraint(plain, other_pk, cipher, is_dec))
        else:
            rnd = self._secret_input_name_factory.add_idf(f'{plain.name if is_param else cipher.name}_R', TypeName.rnd_type())
            pk = self._require_public_key_for_label_at(stmt, new_privacy)
            if not is_dec:
                self.phi.append(CircComment(f'{cipher.name} = enc({plain.name}, {pk.name})'))
            self._phi.append(CircEncConstraint(plain, rnd, pk, cipher, is_dec))

    def _require_secret_key(self) -> HybridArgumentIdf:
        self._need_secret_key = True
        return HybridArgumentIdf(self.get_own_secret_key_name(), TypeName.key_type(), HybridArgType.PRIV_CIRCUIT_VAL)

    def _require_public_key_for_label_at(self, stmt: Optional[Statement], privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        """
        Make circuit helper aware, that the key corresponding to privacy is required at stmt.

        If privacy is not a statically known label, the key is requested on spot.
        Otherwise the label is added to the global key set.
        The keys in that set are requested only once at the start of the external wrapper function, to improve efficiency.

        Note: This function has side effects on stmt (adds a pre_statement)

        :return: HybridArgumentIdf which references the key
        """
        if privacy in self._static_owner_labels:
            # Statically known privacy -> keep track (all global keys will be requested only once)
            self._global_keys[privacy] = None
            return HybridArgumentIdf(self.get_glob_key_name(privacy), TypeName.key_type(), HybridArgType.PUB_CIRCUIT_ARG)

        if stmt is None:
            raise ValueError('stmt cannot be None if privacy is not guaranteed to be statically known')

        # Dynamic privacy -> always request key on spot and add to local in args
        name = f'{self._in_name_factory.get_new_name(TypeName.key_type())}_{privacy.name}'
        idf, get_key_stmt = self.request_public_key(privacy, name)
        stmt.pre_statements.append(get_key_stmt)
        return idf

    def _get_public_key_in_sender_field(self, stmt: Statement, cipher: HybridArgumentIdf) -> HybridArgumentIdf:
        """
        Ensure the circuit has access to the public key stored in cipher's sender field.

        Note: This function has side effects on stmt [adds a pre-statement]

        :param stmt [SIDE EFFECT]: statement in which this private expression occurs
        :param cipher: HybridArgumentIdf which references the cipher value
        :return: HybridArgumentIdf which references the key in cipher's sender field (or 0 if none)
        """
        name = f'{self._in_name_factory.get_new_name(TypeName.key_type())}_sender'
        key_idf = self._in_name_factory.add_idf(name, TypeName.key_type())
        key_expr = KeyLiteralExpr([cipher.get_loc_expr(stmt).index(cfg.cipher_payload_len)]).as_type(TypeName.key_type())
        stmt.pre_statements.append(AssignmentStatement(key_idf.get_loc_expr(), key_expr))
        return key_idf
