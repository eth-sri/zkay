from typing import List, Dict, Optional, Tuple, Callable, Set, Union

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
    StructDefinition, SliceExpr, Statement, StateVariableDeclaration, IfStatement, TupleExpr, VariableDeclaration, Mapping, IndexExpr
from zkay.zkay_ast.visitor.deep_copy import deep_copy


class CircuitHelper:
    def __init__(self, fct: ConstructorOrFunctionDefinition,
                 static_owner_labels: List[PrivacyLabelExpr],
                 expr_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 circ_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 internal_circuit: Optional['CircuitHelper'] = None):
        super().__init__()

        # Function and verification contract corresponding to this circuit
        self.fct = fct
        self.verifier_contract_filename: Optional[str] = None
        self.verifier_contract_type: Optional[UserDefinedTypeName] = None
        self.internal_zk_data_struct: Optional[StructDefinition] = None

        # Transformer visitors
        self._expr_trafo: AstTransformerVisitor = expr_trafo_constructor(self)
        self._circ_trafo: AstTransformerVisitor = circ_trafo_constructor(self)

        # List of proof circuit statements (assertions and assignments)
        self._phi: List[CircuitStatement] = []

        # Local variables outside circuit (for inlining)
        self._local_var_name_factory = NameFactory('_zk_tmp', arg_type=HybridArgType.PUB_CONTRACT_VAL)

        # Private circuit inputs
        self._secret_input_name_factory = NameFactory('secret', arg_type=HybridArgType.PRIV_CIRCUIT_VAL)

        # Circuit internal variables
        self._circ_temp_name_factory = NameFactory('tmp', arg_type=HybridArgType.TMP_CIRCUIT_VAL)

        # Public circuit inputs
        self._out_name_factory = NameFactory(cfg.zk_out_name, arg_type=HybridArgType.PUB_CIRCUIT_ARG)
        self._in_name_factory = NameFactory(cfg.zk_in_name, arg_type=HybridArgType.PUB_CIRCUIT_ARG)

        # For a given owner label (idf or me), stores the corresponding assignment of the requested key to the corresponding in variable
        self._static_owner_labels = static_owner_labels
        self._global_keys: Set[Union[MeExpr, Identifier]] = set()

        self.has_return_var = False
        self.function_calls_with_verification: List[FunctionCallExpr] = []

        # Set by transform_transitive_calls
        if internal_circuit:
            self.verifier_contract_filename = internal_circuit.verifier_contract_filename
            internal_circuit.verifier_contract_filename = None
            self.verifier_contract_type = internal_circuit.verifier_contract_type
            internal_circuit.verifier_contract_type = None
            self._global_keys = internal_circuit._global_keys

            self.trans_priv_size = internal_circuit.priv_in_size_trans
            self.trans_in_size = internal_circuit.in_size_trans
            self.trans_out_size = internal_circuit.out_size_trans
        else:
            self.trans_priv_size, self.trans_in_size, self.trans_out_size = None, None, None

        # Current inlining remapping dictionary (is_local, name)
        # (if is_local = true, it does not persist after current inline function returns)
        self._inline_var_remap: Dict[Tuple[bool, str], HybridArgumentIdf] = {}

    def get_circuit_name(self) -> str:
        return '' if self.verifier_contract_type is None else self.verifier_contract_type.code()

    @property
    def zk_data_struct_name(self):
        return f'{self.fct.unambiguous_name}_{cfg.zk_struct_suffix}'

    @property
    def priv_in_size_trans(self) -> int:
        return self.priv_in_size + self.trans_priv_size

    @property
    def priv_in_size(self) -> int:
        return self._secret_input_name_factory.size

    @property
    def out_size_trans(self) -> int:
        return self.out_size + self.trans_out_size

    @property
    def out_size(self) -> int:
        return self._out_name_factory.size

    @property
    def in_size_trans(self) -> int:
        return self.in_size + self.trans_in_size

    @property
    def in_size(self) -> int:
        return self._in_name_factory.size

    @property
    def output_idfs(self) -> List[HybridArgumentIdf]:
        return self._out_name_factory.idfs

    @property
    def input_idfs(self) -> List[HybridArgumentIdf]:
        return self._in_name_factory.idfs

    @property
    def sec_idfs(self) -> List[HybridArgumentIdf]:
        return self._secret_input_name_factory.idfs

    @property
    def phi(self) -> List[CircuitStatement]:
        return self._phi

    @property
    def requested_global_keys(self) -> Set[Union[MeExpr, Identifier]]:
        return self._global_keys

    @property
    def public_arg_arrays(self) -> List[Tuple[str, int]]:
        """ Returns names and lengths of all public parameter uint256 arrays which go into the verifier"""
        return [(self._in_name_factory.base_name, self.in_size_trans), (self._out_name_factory.base_name, self.out_size_trans)]

    @staticmethod
    def _get_privacy_expr_from_label(plabel: PrivacyLabelExpr):
        if isinstance(plabel, Identifier):
            return IdentifierExpr(plabel.clone(), AnnotatedTypeName.address_all()).override(target=plabel.parent)
        else:
            return plabel.clone()

    def lookup_privacy_label(self, analysis, privacy):
        """
            If privacy is equivalent to a static privacy label or MeExpr (according to program analysis)
            -> Return the corresponding static label, otherwise itself
        """
        for owner in self._static_owner_labels:
            if analysis.same_partition(owner, privacy):
                return owner
        return privacy

    def requires_verification(self) -> bool:
        """ Returns true if the function corresponding to this circuit requires a zk proof verification for correctness """
        req = self.in_size_trans > 0 or self.out_size_trans > 0 or self.priv_in_size_trans > 0
        assert req == self.fct.requires_verification
        return req

    def ensure_parameter_encryption(self, fct: ConstructorOrFunctionDefinition, param: Parameter, offset) -> AssignmentStatement:
        plain_idf = self._secret_input_name_factory.add_idf(param.idf.name, param.original_type.type_name)
        name = f'{self._in_name_factory.get_new_name(param.annotated_type.type_name, False)}_{param.idf.name}'
        cipher_idf = self._in_name_factory.add_idf(name, param.annotated_type.type_name)
        self._ensure_encryption(fct.body, plain_idf, Expression.me_expr(), cipher_idf, True, False)
        return SliceExpr(IdentifierExpr(cfg.zk_in_name), None, offset, cipher_idf.t.size_in_uints).assign(SliceExpr(IdentifierExpr(param.idf.clone()), None, 0, cipher_idf.t.size_in_uints))

    def evaluate_expr_in_circuit(self, expr: Expression, new_privacy: PrivacyLabelExpr) -> LocationExpr:
        assert not self._inline_var_remap
        with InlineRemap(self, persist_globals=False):
            return self._get_circuit_output_for_private_expression(expr, new_privacy)

    def evaluate_stmt_in_circuit(self, ast: Statement):
        assert not self._inline_var_remap
        with InlineRemap(self, persist_globals=False):
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

            ret_args = self.inline_circuit_function(fcall, fdef)
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
            self._ensure_encryption(expr.statement, locally_decrypted_idf, Expression.me_expr(), input_idf, False, True)

        self._phi.append(CircComment(f'{input_idf.name} (dec: {locally_decrypted_idf.name}) = {expr_text}'))
        expr.statement.pre_statements.append(CircuitInputStatement(input_idf.get_loc_expr(), input_expr))
        return locally_decrypted_idf, locally_decrypted_idf.get_loc_expr()

    def call_function(self, ast: FunctionCallExpr):
        assert ast.func.target.requires_verification
        self.function_calls_with_verification.append(ast)
        self.phi.append(CircCall(ast.func.target))

    # For inlining
    # prepend:
    # 1. assign args to temporary variables
    # 2. include original function body with replaced parameter idfs
    # 3. assign return value to temporary var
    # return temp ret var

    def inline_circuit_function(self, ast: FunctionCallExpr, fdef: ConstructorOrFunctionDefinition) -> TupleExpr:
        assert not fdef.is_constructor
        with InlineRemap(self, persist_globals=True):
            with CircIndentBlockBuilder(f'INLINED {ast.code()}', self._phi):
                for param, arg in zip(fdef.parameters, ast.args):
                    self.create_temporary_circuit_variable(Identifier(param.idf.name), arg)
                inlined_body = deep_copy(fdef.original_body, with_types=True, with_analysis=True)
                self._circ_trafo.visit(inlined_body)
                ast.statement.pre_statements += inlined_body.pre_statements
                ret_idfs = [self._inline_var_remap[(True, f'{cfg.return_var_name}_{idx}')] for idx in range(len(fdef.return_parameters))]
                ret = TupleExpr([IdentifierExpr(idf.clone()).as_type(idf.t) for idf in ret_idfs])
        if len(ret.elements) == 1:
            ret = ret.elements[0]
        return ret

    def get_remapped_idf(self, idf: Identifier, is_local: bool) -> Union[HybridArgumentIdf, Identifier]:
        return self._inline_var_remap.get((is_local, idf.name), idf)

    def get_remapped_idf_expr(self, idf: IdentifierExpr) -> LocationExpr:
        is_local = not isinstance(idf.target, StateVariableDeclaration)
        remapped_idf = self.get_remapped_idf(idf.idf, is_local)
        return idf if remapped_idf == idf.idf else remapped_idf.get_loc_expr(idf.parent).as_type(idf.annotated_type)

    def create_temporary_circuit_variable(self, orig_idf: Identifier, expr: Expression, is_local: bool = True):
        tmp_var, _ = self._evaluate_private_expression(expr, tmp_suffix=f'_{orig_idf.name}')
        self._inline_var_remap[(is_local, orig_idf.name)] = tmp_var

    def _add_assign(self, lhs: Expression, rhs: Expression):
        if isinstance(lhs, IdentifierExpr): # for now no ref types
            self.create_temporary_circuit_variable(lhs.idf, rhs, is_local=not isinstance(lhs.target, StateVariableDeclaration))
        elif isinstance(lhs, IndexExpr):
            raise NotImplementedError()
        else:
            assert isinstance(lhs, TupleExpr)
            if isinstance(rhs, FunctionCallExpr):
                rhs = self._circ_trafo.visit(rhs)
            assert isinstance(rhs, TupleExpr) and len(lhs.elements) == len(rhs.elements)
            for e_l, e_r in zip(lhs.elements, rhs.elements):
                self._add_assign(e_l, e_r)

    def add_assignment_to_circuit(self, ast: AssignmentStatement):
        self._add_assign(ast.lhs, ast.rhs)

    def add_if_statement_to_circuit(self, ast: IfStatement):
        with CircIndentBlockBuilder(f'if {ast.condition.code()}', self.phi):
            cond, _ = self._evaluate_private_expression(ast.condition)
            self._phi.append(CircComment(f'if ({cond.name})'))

            # handle if branch
            prev_remap = self._inline_var_remap.copy()
            with Guarded(self, cond, True):
                self._circ_trafo.visit(ast.then_branch)
            then_remap = self._inline_var_remap.copy()

            # handle else branch
            self._inline_var_remap = prev_remap
            if ast.else_branch is not None:
                self._phi.append(CircComment(f'else ({cond.name})'))
                with Guarded(self, cond, False):
                    self._circ_trafo.visit(ast.else_branch)
            else_remap = self._inline_var_remap.copy()

            # SSA join branches (if both branches write to same external value -> cond assignment to select correct version)
            self._inline_var_remap = {}
            self._phi.append(CircComment(f'join ({cond.name})'))
            for key, val in then_remap.items():
                if key not in else_remap or else_remap[key].name == val.name:
                    self._inline_var_remap[key] = val
                else:
                    # Add conditional assignment and remap to its result
                    then_idf = then_remap[key]
                    else_idf = else_remap[key]
                    rhs = IdentifierExpr(cond.clone(), AnnotatedTypeName(TypeName.bool_type(), Expression.me_expr())).ite(IdentifierExpr(then_idf).as_type(then_idf.t), IdentifierExpr(else_idf).as_type(else_idf.t))
                    rhs = rhs.as_type(then_idf.t)
                    self.create_temporary_circuit_variable(Identifier(key[1]), rhs, is_local=key[0])

    def _get_circuit_output_for_private_expression(self, expr: Expression, new_privacy: PrivacyLabelExpr) -> LocationExpr:
        """
        Corresponds to out() from paper
        :param expr: The expression which should be evaluated privately
        :param new_privacy: The circuit output should be encrypted for this owner (or plain if 'all')
        :return: Location expression which references the encrypted circuit result
        """
        ecode = expr.code()
        with CircIndentBlockBuilder(f'{ecode}', self._phi):
            is_circ_val = isinstance(expr, IdentifierExpr) and isinstance(expr.idf, HybridArgumentIdf) and expr.idf.arg_type != HybridArgType.PUB_CONTRACT_VAL
            if is_circ_val or expr.annotated_type.is_private() or expr.evaluate_privately:
                plain_result_idf, private_expr = self._evaluate_private_expression(expr)
            else:
                plain_result_idf, private_expr = self.add_to_circuit_inputs(expr)

            if isinstance(new_privacy, AllExpr):
                new_out_param = self._out_name_factory.get_new_idf(expr.annotated_type.type_name, private_expr)
                self._phi.append(CircEqConstraint(plain_result_idf, new_out_param))
                out_var = new_out_param.get_loc_expr().implicitly_converted(expr.annotated_type.type_name)
            else:
                new_privacy = self.lookup_privacy_label(expr.analysis, new_privacy)
                privacy_label_expr = self._get_privacy_expr_from_label(new_privacy)
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
        tname = f'{self._circ_temp_name_factory.get_new_name(expr.annotated_type.type_name, False)}{tmp_suffix}'
        sec_circ_var_idf = self._circ_temp_name_factory.add_idf(tname, expr.annotated_type.type_name, priv_expr)
        stmt = CircVarDecl(sec_circ_var_idf, priv_expr)
        self.phi.append(stmt)
        return sec_circ_var_idf, priv_expr

    def _ensure_encryption(self, stmt: Statement, plain: HybridArgumentIdf, new_privacy: PrivacyLabelExpr, cipher: HybridArgumentIdf, is_param: bool, is_dec: bool):
        rnd = self._secret_input_name_factory.add_idf(f'{plain.name if is_param else cipher.name}_R', TypeName.rnd_type())
        pk = self._request_public_key(stmt, new_privacy)
        self._phi.append(CircEncConstraint(plain, rnd, pk, cipher, is_dec))

    def _request_public_key(self, stmt: Statement, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        is_static = isinstance(privacy, IdentifierExpr) and isinstance(privacy.target, StateVariableDeclaration) and privacy.target.is_final
        if isinstance(privacy, MeExpr) or is_static:
            # Global static privacy (either me or final state var)
            self._global_keys.add(privacy)
            return HybridArgumentIdf(self.get_glob_key_name(privacy), TypeName.key_type(), HybridArgType.PUB_CIRCUIT_ARG)

        # Dynamic privacy -> always request key on spot and add to local in args
        name = f'{self._in_name_factory.get_new_name(TypeName.key_type(), False)}_{privacy.name}'
        idf, get_key_stmt = self.request_public_key(privacy, name)
        stmt.pre_statements.append(get_key_stmt)
        return idf

    @staticmethod
    def get_glob_key_name(label: Union[MeExpr, Identifier]):
        assert isinstance(label, (MeExpr, Identifier))
        return f'glob_key_{label.name}'

    def request_public_key(self, plabel: Union[MeExpr, Identifier], name):
        idf = self._in_name_factory.add_idf(name, TypeName.key_type())
        pki = IdentifierExpr(get_contract_instance_idf(cfg.pki_contract_name))
        privacy_label_expr = self._get_privacy_expr_from_label(plabel)
        return idf, idf.get_loc_expr().assign(pki.call('getPk', [self._expr_trafo.visit(privacy_label_expr)]))


class CircIndentBlockBuilder:
    def __init__(self, name: str, phi: List[CircuitStatement]):
        self.name = name
        self.phi = phi
        self.old_phi = None

    def __enter__(self):
        self.old_phi = self.phi[:]

    def __exit__(self, t, value, traceback):
        self.phi[:] = self.old_phi + [CircIndentBlock(self.name, self.phi[len(self.old_phi):])]


class InlineRemap:
    def __init__(self, c: CircuitHelper, *, persist_globals):
        self.c = c
        self.persist_globals = persist_globals
        self.prev: Optional[Dict] = None

    def __enter__(self):
        self.prev = self.c._inline_var_remap.copy()

    def __exit__(self, t, value, traceback):
        if self.persist_globals:
            self.prev.update({(is_loc, key): val for (is_loc, key), val in self.c._inline_var_remap.items() if not is_loc})
        self.c._inline_var_remap = self.prev


class Guarded:
    def __init__(self, c: CircuitHelper, guard_idf: HybridArgumentIdf, is_true: bool) -> None:
        super().__init__()
        self.c = c
        self.guard_idf = guard_idf
        self.is_true = is_true

    def __enter__(self):
        self.c.phi.append(CircGuardModification.add_guard(self.guard_idf, self.is_true))

    def __exit__(self, t, value, traceback):
        self.c.phi.append(CircGuardModification.pop_guard())
