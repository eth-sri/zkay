from typing import List, Dict, Optional, Tuple, Callable, Set, Union

from zkay.config import cfg
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircuitStatement, CircEncConstraint, CircVarDecl, \
    CircEqConstraint, CircComment, CircIndentBlock, CircGuardModification, CircCall
from zkay.compiler.privacy.circuit_generation.name_factory import NameFactory
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.zkay_ast.ast import Expression, IdentifierExpr, PrivacyLabelExpr, \
    LocationExpr, TypeName, AssignmentStatement, UserDefinedTypeName, ConstructorOrFunctionDefinition, Parameter, \
    HybridArgumentIdf, EncryptionExpression, FunctionCallExpr, FunctionDefinition, VariableDeclarationStatement, \
    Identifier, AnnotatedTypeName, HybridArgType, CircuitInputStatement, CircuitComputationStatement, AllExpr, MeExpr, \
    StructDefinition, SliceExpr, Statement, StateVariableDeclaration, IfStatement, TupleExpr, VariableDeclaration, \
    ReturnStatement, Block, MemberAccessExpr


class CircuitHelper:
    def __init__(self, fct: ConstructorOrFunctionDefinition,
                 static_owner_labels: List[Union[MeExpr, AllExpr, Identifier]],
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
        self._circ_temp_name_factory = NameFactory('tmp', arg_type=HybridArgType.PRIV_CIRCUIT_VAL)

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

        # Current inlining remapping dictionary
        # (maps inlined function parameter and variable identifiers to the corresponding temporary variables)
        self._inline_var_remap: Dict[str, HybridArgumentIdf] = {}

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
            return IdentifierExpr(plabel.clone(), AnnotatedTypeName.address_all()).with_target(plabel.parent)
        else:
            return plabel.clone()

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

    def get_circuit_output_for_private_expression(self, expr: Expression, new_privacy: PrivacyLabelExpr) -> LocationExpr:
        """
        Corresponds to out() from paper
        :param expr: The expression which should be evaluated privately
        :param new_privacy: The circuit output should be encrypted for this owner (or plain if 'all')
        :return: Location expression which references the encrypted circuit result
        """
        ecode = expr.code()
        with CircIndentBlockBuilder(f'{ecode}', self._phi):
            if expr.annotated_type.is_public() and not expr.evaluate_privately:
                plain_result_idf, private_expr = self.add_to_circuit_inputs(expr)
            else:
                plain_result_idf, private_expr = self._evaluate_private_expression(expr)

            if isinstance(new_privacy, AllExpr):
                new_out_param = self._out_name_factory.get_new_idf(expr.annotated_type.type_name, private_expr)
                self._phi.append(CircEqConstraint(plain_result_idf, new_out_param))
                out_var = new_out_param.get_loc_expr().implicitly_converted(expr.annotated_type.type_name)
            else:
                for owner in self._static_owner_labels:
                    if expr.statement.before_analysis.same_partition(owner, new_privacy):
                        new_privacy = owner
                        break
                privacy_label_expr = self._get_privacy_expr_from_label(new_privacy)
                new_out_param = self._out_name_factory.get_new_idf(TypeName.cipher_type(), EncryptionExpression(private_expr, privacy_label_expr))
                self._ensure_encryption(expr.statement, plain_result_idf, new_privacy, new_out_param, False, False)
                out_var = new_out_param.get_loc_expr()

        self._phi.append(CircComment(f'{new_out_param.name} = {ecode}\n'))

        expr.statement.pre_statements.append(CircuitComputationStatement(new_out_param))
        return out_var

    def evaluate_if_stmt_in_circuit(self, ast: IfStatement):
        assert ast.condition.annotated_type.is_private()
        args = []
        arg_names = set()
        for var in ast.read_values:
            if var.in_scope_at(ast): # defined outside if statement -> need to be passed in as arg
                assert var.target.annotated_type.type_name.can_be_private()
                assert isinstance(var.target, (Parameter, VariableDeclaration, StateVariableDeclaration))
                args.append(IdentifierExpr(var.target.idf.clone(), var.target.annotated_type.clone()).with_target(var.target))
                arg_names.add(var.target.idf.name)
                # technically only need to add those, which are not written before they are read

        ret_params = []
        for var in ast.modified_values:
            if var.in_scope_at(ast): # side effect visible outside -> return it
                assert var.target.annotated_type.is_private()
                assert var.target.annotated_type.type_name.can_be_private()
                assert isinstance(var.target, (Parameter, VariableDeclaration, StateVariableDeclaration))
                ret_params.append(IdentifierExpr(var.target.idf.clone(), var.target.annotated_type.clone()).with_target(var.target))

        astmt = AssignmentStatement(None, None)
        fdef = FunctionDefinition(Identifier('<if_fct>'),
                                  [Parameter([], arg.annotated_type, arg.idf.clone()) for arg in args], ['private'],
                                  [Parameter([], ret.annotated_type, ret.idf.clone()) for ret in ret_params], Block([
            ast,
            ReturnStatement(TupleExpr(ret_params))
        ]))
        fcall = FunctionCallExpr(IdentifierExpr('<if_fct>'), args)
        fcall.statement = astmt

        ret_args = self.inline_circuit_function(fcall, fdef)
        ret_arg_outs = [
            self.get_circuit_output_for_private_expression(ret_arg, ret_param.annotated_type.privacy_annotation.privacy_annotation_label())
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

    def inline_circuit_function(self, ast: FunctionCallExpr, fdef: FunctionDefinition) -> TupleExpr:
        with InlineRemap(self):
            with CircIndentBlockBuilder(f'INLINED {ast.code()}', self._phi):
                for param, arg in zip(fdef.parameters, ast.args):
                    self.create_temporary_circuit_variable(Identifier(param.idf.name).decl_var(param.annotated_type, arg))
                inlined_stmts = fdef.original_body.clone().statements
                for stmt in inlined_stmts:
                    self._circ_trafo.visit(stmt)
                    ast.statement.pre_statements += stmt.pre_statements
                ret_idfs = [self._inline_var_remap[f'{cfg.return_var_name}_{idx}'] for idx in range(len(fdef.return_parameters))]
                ret = TupleExpr([IdentifierExpr(idf.clone()).as_type(idf.t) for idf in ret_idfs])
        if len(ret.elements) == 1:
            ret = ret.elements[0]
        return ret

    def get_remapped_idf(self, idf: Identifier) -> Union[HybridArgumentIdf, Identifier]:
        while idf.name in self._inline_var_remap:
            idf = self._inline_var_remap[idf.name]
        return idf

    def get_remapped_idf_expr(self, idf: IdentifierExpr) -> LocationExpr:
        if idf.idf.name not in self._inline_var_remap:
            return idf
        return idf.replaced_with(self.get_remapped_idf(idf.idf).get_loc_expr()).as_type(idf.annotated_type)

    def create_temporary_circuit_variable(self, ast: VariableDeclarationStatement):
        tmp_var, _ = self._evaluate_private_expression(ast.expr, tmp_suffix=f'_{ast.variable_declaration.idf.name}')
        self._inline_var_remap[self.get_remapped_idf(ast.variable_declaration.idf).name] = tmp_var

    def _add_assign(self, lhs: Expression, rhs: Expression):
        if isinstance(lhs, IdentifierExpr): # for now no ref types
            self.create_temporary_circuit_variable(lhs.idf.decl_var(lhs.target.annotated_type.clone(), rhs))
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
        raise NotImplementedError()

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
    def __init__(self, c: CircuitHelper):
        self.c = c
        self.prev = None

    def __enter__(self):
        self.prev = self.c._inline_var_remap.copy()

    def __exit__(self, t, value, traceback):
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
