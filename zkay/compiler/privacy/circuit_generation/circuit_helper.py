from collections import OrderedDict
from contextlib import contextmanager
from typing import List, Optional, Tuple, Callable, Union, ContextManager

from zkay.compiler.name_remapper import CircVarRemapper
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircuitStatement, CircEncConstraint, CircVarDecl, \
    CircEqConstraint, CircComment, CircIndentBlock, CircGuardModification, CircCall
from zkay.compiler.privacy.circuit_generation.name_factory import NameFactory
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.config import cfg
from zkay.zkay_ast.ast import Expression, IdentifierExpr, PrivacyLabelExpr, \
    LocationExpr, TypeName, AssignmentStatement, UserDefinedTypeName, ConstructorOrFunctionDefinition, Parameter, \
    HybridArgumentIdf, EncryptionExpression, FunctionCallExpr, Identifier, AnnotatedTypeName, HybridArgType, CircuitInputStatement, \
    CircuitComputationStatement, AllExpr, MeExpr, ReturnStatement, Block, MemberAccessExpr, NumberLiteralType, BooleanLiteralType, \
    SliceExpr, Statement, StateVariableDeclaration, IfStatement, TupleExpr, VariableDeclaration, IndexExpr, get_privacy_expr_from_label
from zkay.zkay_ast.visitor.deep_copy import deep_copy


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

        self._global_keys: OrderedDict[Union[MeExpr, Identifier], None] = OrderedDict([])
        """Set of statically known privacy labels (OrderedDict is used to ensure deterministic iteration order)"""

        self.function_calls_with_verification: List[FunctionCallExpr] = []
        """
        List of all (non-transitive) calls in self.fct's body to functions which require verification, in AST visiting order
        This is internally used to compute transitive in/out/privin sizes, but may also be useful when implementing a new
        circuit generator backend.
        """

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
        return f'{self.fct.unambiguous_name}_{cfg.zk_struct_suffix}'

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
    def circ_indent_block(self, name: str):
        """
        Return context manager which manages the lifetime of a CircIndentBlock.

        All statements which are inserted into self.phi during the lifetime of this context manager are automatically wrapped inside
        a CircIndentBlock statement with the supplied name.
        """
        old_phi = self.phi[:]
        yield
        self.phi[:] = old_phi + [CircIndentBlock(name, self.phi[len(old_phi):])]

    def guarded(self, guard_idf: HybridArgumentIdf, is_true: bool) -> ContextManager:
        """Return a context manager which manages the lifetime of a guard variable."""
        return CircGuardModification.guarded(self.phi, guard_idf, is_true)

    @staticmethod
    def get_glob_key_name(label: PrivacyLabelExpr):
        """Return the name of the HybridArgumentIdf which holds the statically known public key for the given privacy label."""
        assert isinstance(label, (MeExpr, Identifier))
        return f'glob_key_{label.name}'

    def requires_verification(self) -> bool:
        """ Returns true if the function corresponding to this circuit requires a zk proof verification for correctness """
        req = self.in_size_trans > 0 or self.out_size_trans > 0 or self.priv_in_size_trans > 0
        assert req == self.fct.requires_verification
        return req

    # Solidity-side interface #

    def ensure_parameter_encryption(self, param: Parameter):
        """
        Make circuit prove that the encryption of the specified parameter is correct.
        """
        assert param.original_type.is_private()

        plain_idf = self._secret_input_name_factory.add_idf(param.idf.name, param.original_type.type_name)
        name = f'{self._in_name_factory.get_new_name(param.annotated_type.type_name)}_{param.idf.name}'
        cipher_idf = self._in_name_factory.add_idf(name, param.annotated_type.type_name)
        self._ensure_encryption(None, plain_idf, Expression.me_expr(), cipher_idf, True, False)

    def evaluate_expr_in_circuit(self, expr: Expression, new_privacy: PrivacyLabelExpr) -> LocationExpr:
        """
            Corresponds to out() from paper
            :param expr: The expression which should be evaluated privately
            :param new_privacy: The circuit output should be encrypted for this owner (or plain if 'all')
            :return: Location expression which references the encrypted circuit result
        """
        assert not self._remapper
        with self._remapper.remap_scope(persist_globals=False):
            return self._get_circuit_output_for_private_expression(expr, new_privacy)

    def evaluate_stmt_in_circuit(self, ast: Statement):
        assert not self._remapper
        with self._remapper.remap_scope(persist_globals=False):
            astmt = AssignmentStatement(None, None)
            astmt.before_analysis = ast.before_analysis

            args = []
            arg_names = set()
            for var in ast.read_values:
                if var.in_scope_at(ast): # defined outside if statement -> need to be passed in as arg
                    assert isinstance(var.target, (Parameter, VariableDeclaration, StateVariableDeclaration))
                    arg = IdentifierExpr(var.target.idf.clone(), var.target.annotated_type.declared_type.clone()).override(target=var.target)
                    arg.statement = astmt
                    args.append(arg)
                    arg_names.add(var.target.idf.name)
                    # technically only need to add those, which are not written before they are read

            ret_params = []
            for var in ast.modified_values:
                if var.in_scope_at(ast): # side effect visible outside -> return it
                    assert ast.before_analysis.same_partition(var.privacy, Expression.me_expr()) # otherwise control flow could potentially leak info to someone
                    assert isinstance(var.target, (Parameter, VariableDeclaration, StateVariableDeclaration))
                    t = var.target.annotated_type.zkay_type.type_name
                    if not t.is_primitive_type():
                        raise NotImplementedError('Reference types inside private if statements are not supported')
                    ret_param = IdentifierExpr(var.target.idf.clone(), AnnotatedTypeName(t, Expression.me_expr())).override(target=var.target)
                    ret_param.statement = astmt
                    ret_params.append(ret_param)

            fdef = ConstructorOrFunctionDefinition(
                Identifier('<stmt_fct>'),
                [Parameter([], arg.annotated_type, arg.idf.clone()) for arg in args], ['private'],
                [Parameter([], ret.annotated_type, ret.idf.clone()) for ret in ret_params],
                Block([ast, ReturnStatement(TupleExpr(ret_params))])
            )
            fdef.original_body = fdef.body
            fdef.body.parent = fdef
            fdef.parent = ast.function.body

            fcall = FunctionCallExpr(IdentifierExpr('<stmt_fct>'), args)
            fcall.statement = astmt

            ret_args = self.inline_function_into_circuit(fcall, fdef)
            if not isinstance(ret_args, TupleExpr):
                ret_args = TupleExpr([ret_args])
            for ret_arg in ret_args.elements:
                ret_arg.statement = astmt
            ret_arg_outs = [
                self._get_circuit_output_for_private_expression(ret_arg, Expression.me_expr())
                for ret_param, ret_arg in zip(ret_params, ret_args.elements)
            ]

            astmt.lhs = TupleExpr([ret_param.clone() for ret_param in ret_params])
            astmt.rhs = TupleExpr(ret_arg_outs)
            return astmt

    def add_to_circuit_inputs(self, expr: Expression) -> Tuple[HybridArgumentIdf, LocationExpr]:
        """
        Corresponds to in() from paper
        :param expr: public expression which should be made available inside the circuit as an argument
        :return: Location expression which references the (decrypted if necessary) input expression
        """
        privacy = Expression.me_expr() if expr.annotated_type.is_private() else Expression.all_expr()

        expr_text = expr.code()
        input_expr = self._expr_trafo.visit(expr)
        t = input_expr.annotated_type.type_name
        if isinstance(t, BooleanLiteralType):
            return self._evaluate_private_expression(input_expr, str(t.value))
        elif isinstance(t, NumberLiteralType):
            return self._evaluate_private_expression(input_expr, str(t.value))

        if privacy.is_all_expr():
            input_idf = self._in_name_factory.get_new_idf(expr.annotated_type.type_name)
            locally_decrypted_idf = input_idf
        else:
            locally_decrypted_idf = self._secret_input_name_factory.get_new_idf(expr.annotated_type.type_name)
            input_idf = self._in_name_factory.get_new_idf(TypeName.cipher_type(), IdentifierExpr(locally_decrypted_idf))
            self._ensure_encryption(None, locally_decrypted_idf, Expression.me_expr(), input_idf, False, True)

        self._phi.append(CircComment(f'{input_idf.name} (dec: {locally_decrypted_idf.name}) = {expr_text}'))
        expr.statement.pre_statements.append(CircuitInputStatement(input_idf.get_loc_expr(), input_expr))
        return locally_decrypted_idf, locally_decrypted_idf.get_loc_expr()

    def call_function(self, ast: FunctionCallExpr):
        assert ast.func.target.requires_verification
        self.function_calls_with_verification.append(ast)
        self.phi.append(CircCall(ast.func.target))

    def request_public_key(self, plabel: Union[MeExpr, Identifier], name):
        idf = self._in_name_factory.add_idf(name, TypeName.key_type())
        pki = IdentifierExpr(get_contract_instance_idf(cfg.pki_contract_name))
        privacy_label_expr = get_privacy_expr_from_label(plabel)
        return idf, idf.get_loc_expr().assign(pki.call('getPk', [self._expr_trafo.visit(privacy_label_expr)]))

    # Circuit-side interface #

    # For inlining
    # prepend:
    # 1. assign args to temporary variables
    # 2. include original function body with replaced parameter idfs
    # 3. assign return value to temporary var
    # return temp ret var

    def get_remapped_idf_expr(self, idf: IdentifierExpr) -> LocationExpr:
        is_local = not isinstance(idf.target, StateVariableDeclaration)
        if self._remapper.is_remapped(idf.idf.name, is_local):
            remapped_idf = self._remapper.get_current(idf.idf.name, is_local)
            return remapped_idf.get_loc_expr(idf.parent).as_type(idf.annotated_type)
        else:
            return idf

    def introduce_temporary_circuit_variable(self, orig_idf: Identifier, expr: Expression, is_local: bool = True):
        tmp_var = self._create_temp_var(orig_idf.name, expr)
        self._remapper.remap(orig_idf.name, is_local, tmp_var)

    def inline_function_into_circuit(self, ast: FunctionCallExpr, fdef: ConstructorOrFunctionDefinition) -> TupleExpr:
        assert not fdef.is_constructor
        with self._remapper.remap_scope(persist_globals=True):
            with self.circ_indent_block(f'INLINED {ast.code()}'):
                for param, arg in zip(fdef.parameters, ast.args):
                    self.introduce_temporary_circuit_variable(Identifier(param.idf.name), arg)
                inlined_body = deep_copy(fdef.original_body, with_types=True, with_analysis=True)
                self._circ_trafo.visit(inlined_body)
                ast.statement.pre_statements += inlined_body.pre_statements
                ret_idfs = [self._remapper.get_current(f'{cfg.return_var_name}_{idx}') for idx in range(len(fdef.return_parameters))]
                ret = TupleExpr([IdentifierExpr(idf.clone()).as_type(idf.t) for idf in ret_idfs])
        if len(ret.elements) == 1:
            ret = ret.elements[0]
        return ret

    def add_assignment_to_circuit(self, ast: AssignmentStatement):
        self._add_assign(ast.lhs, ast.rhs)

    def add_if_statement_to_circuit(self, ast: IfStatement):
        with self.circ_indent_block(f'if {ast.condition.code()}'):
            cond, _ = self._evaluate_private_expression(ast.condition)

            # Handle if branch
            with self._remapper.remap_scope(persist_globals=False):
                self._phi.append(CircComment(f'if ({cond.name})'))
                with self.guarded(cond, True):
                    self._circ_trafo.visit(ast.then_branch)
                then_remap = self._remapper.get_state()

            # Handle else branch
            if ast.else_branch is not None:
                self._phi.append(CircComment(f'else ({cond.name})'))
                with self.guarded(cond, False):
                    self._circ_trafo.visit(ast.else_branch)

            # SSA join branches (if both branches write to same external value -> cond assignment to select correct version)
            self._phi.append(CircComment(f'join ({cond.name})'))
            true_cond = IdentifierExpr(cond.clone(), AnnotatedTypeName(TypeName.bool_type(), Expression.me_expr()))
            self._remapper.join_branch(true_cond, then_remap, self._create_temp_var)

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

    def _create_temp_var(self, orig_idf_name: str, expr: Expression) -> HybridArgumentIdf:
        return self._evaluate_private_expression(expr, tmp_suffix=f'_{orig_idf_name}')[0]

    def _add_assign(self, lhs: Expression, rhs: Expression):
        if isinstance(lhs, IdentifierExpr): # for now no ref types
            self.introduce_temporary_circuit_variable(lhs.idf, rhs, is_local=not isinstance(lhs.target, StateVariableDeclaration))
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
        ecode = expr.code()
        with self.circ_indent_block(f'{ecode}'):
            is_circ_val = isinstance(expr, IdentifierExpr) and isinstance(expr.idf, HybridArgumentIdf) and expr.idf.arg_type != HybridArgType.PUB_CONTRACT_VAL
            if is_circ_val or expr.annotated_type.is_private() or expr.evaluate_privately:
                plain_result_idf, private_expr = self._evaluate_private_expression(expr)
            else:
                plain_result_idf, private_expr = self.add_to_circuit_inputs(expr)

            if isinstance(new_privacy, AllExpr):
                new_out_param = self._out_name_factory.get_new_idf(expr.annotated_type.type_name, private_expr)
                self._phi.append(CircEqConstraint(plain_result_idf, new_out_param))
                out_var = new_out_param.get_loc_expr().explicitly_converted(expr.annotated_type.type_name)
            else:
                new_privacy = self._get_canonical_privacy_label(expr.analysis, new_privacy)
                privacy_label_expr = get_privacy_expr_from_label(new_privacy)
                new_out_param = self._out_name_factory.get_new_idf(TypeName.cipher_type(), EncryptionExpression(private_expr, privacy_label_expr))
                self._ensure_encryption(expr.statement, plain_result_idf, new_privacy, new_out_param, False, False)
                out_var = new_out_param.get_loc_expr()

        self._phi.append(CircComment(f'{new_out_param.name} = {ecode}\n'))

        expr.statement.pre_statements.append(CircuitComputationStatement(new_out_param))
        return out_var

    def _evaluate_private_expression(self, expr: Expression, tmp_suffix=''):
        assert not (isinstance(expr, MemberAccessExpr) and isinstance(expr.member, HybridArgumentIdf))
        if isinstance(expr, IdentifierExpr) and isinstance(expr.idf, HybridArgumentIdf) \
                and expr.idf.arg_type != HybridArgType.PUB_CONTRACT_VAL:
            # Already evaluated in circuit
            return expr.idf.clone(), expr

        priv_expr = self._circ_trafo.visit(expr)
        tname = f'{self._circ_temp_name_factory.get_new_name(expr.annotated_type.type_name)}{tmp_suffix}'
        sec_circ_var_idf = self._circ_temp_name_factory.add_idf(tname, expr.annotated_type.type_name, priv_expr)
        stmt = CircVarDecl(sec_circ_var_idf, priv_expr)
        self.phi.append(stmt)
        return sec_circ_var_idf, priv_expr

    def _ensure_encryption(self, stmt: Optional[Statement], plain: HybridArgumentIdf, new_privacy: PrivacyLabelExpr,
                           cipher: HybridArgumentIdf, is_param: bool, is_dec: bool):
        rnd = self._secret_input_name_factory.add_idf(f'{plain.name if is_param else cipher.name}_R', TypeName.rnd_type())
        pk = self._require_public_key_for_label_at(stmt, new_privacy)
        self._phi.append(CircEncConstraint(plain, rnd, pk, cipher, is_dec))

    def _require_public_key_for_label_at(self, stmt: Optional[Statement], privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
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
