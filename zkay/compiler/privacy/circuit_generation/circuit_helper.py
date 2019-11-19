from typing import List, Dict, Optional, Tuple, Callable

import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircuitStatement, EncConstraint, TempVarDecl, \
    EqConstraint, CircAssignment, CircComment, CircIndentBlock
from zkay.compiler.privacy.circuit_generation.name_factory import NameFactory
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.zkay_ast.ast import Expression, IdentifierExpr, PrivacyLabelExpr, \
    LocationExpr, TypeName, AssignmentStatement, UserDefinedTypeName, ConstructorOrFunctionDefinition, Parameter, \
    HybridArgumentIdf, EncryptionExpression, FunctionCallExpr, FunctionDefinition, VariableDeclarationStatement, Identifier, \
    AnnotatedTypeName, IndentBlock, HybridArgType, CircuitInputStatement, CircuitComputationStatement, BlankLine


class CircuitHelper:
    def __init__(self, fct: ConstructorOrFunctionDefinition,
                 inline_stmt_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 expr_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 circ_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor]):
        super().__init__()

        # Function and verification contract corresponding to this circuit
        self.fct = fct
        self.verifier_contract_filename: Optional[str] = None
        self.verifier_contract_type: Optional[UserDefinedTypeName] = None

        # Transformer visitors
        self._inline_stmt_trafo: AstTransformerVisitor = inline_stmt_trafo_constructor(self)
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
        self._pk_for_label: Dict[str, AssignmentStatement] = {}

        self._param_to_in_assignments: List[AssignmentStatement] = []
        self.has_return_var = False

        # Current inlining remapping dictionary
        # (maps inlined function parameter and variable identifiers to the corresponding temporary variables)
        self._inline_var_remap: Dict[str, HybridArgumentIdf] = {}

    def get_circuit_name(self) -> str:
        return '' if self.verifier_contract_type is None else self.verifier_contract_type.code()

    @staticmethod
    def get_transformed_type(expr: Expression, privacy: PrivacyLabelExpr) -> TypeName:
        return expr.annotated_type.type_name if privacy.is_all_expr() else TypeName.cipher_type()

    @property
    def num_public_args(self) -> int:
        return self._out_name_factory.count + self._in_name_factory.count

    @property
    def has_out_args(self) -> bool:
        return self._out_name_factory.count > 0

    @property
    def has_in_args(self) -> bool:
        return self._in_name_factory.count > 0

    @property
    def public_out_size(self) -> int:
        return self._out_name_factory.size

    @property
    def output_idfs(self) -> List[HybridArgumentIdf]:
        return self._out_name_factory.idfs

    @property
    def input_idfs(self) -> List[HybridArgumentIdf]:
        return self._in_name_factory.idfs

    @property
    def temp_vars_outside_circuit(self) -> List[HybridArgumentIdf]:
        return self._local_var_name_factory.idfs

    @property
    def sec_idfs(self) -> List[HybridArgumentIdf]:
        return self._secret_input_name_factory.idfs

    @property
    def phi(self) -> List[CircuitStatement]:
        return self._phi

    @property
    def public_key_requests(self) -> List[AssignmentStatement]:
        return list(self._pk_for_label.values())

    @property
    def param_to_in_assignments(self) -> List[AssignmentStatement]:
        return self._param_to_in_assignments

    @property
    def public_arg_arrays(self) -> List[Tuple[str, int]]:
        """ Returns names and lengths of all public parameter uint256 arrays which go into the verifier"""
        return [(e.base_name, e.size) for e in (self._in_name_factory, self._out_name_factory) if e.count > 0]

    def requires_verification(self) -> bool:
        """ Returns true if the function corresponding to this circuit requires a zk proof verification for correctness """
        req = self.has_in_args or self.has_out_args or self._secret_input_name_factory.count
        assert req == self.fct.requires_verification_if_external # TODO -> requires_verification
        return req

    def ensure_parameter_encryption(self, param: Parameter):
        plain_idf = self._secret_input_name_factory.add_idf(param.idf.name, param.annotated_type.type_name)
        cipher_idf = self._in_name_factory.get_new_idf(TypeName.cipher_type())
        self._ensure_encryption(plain_idf, Expression.me_expr(), cipher_idf, True)
        self._param_to_in_assignments.append(cipher_idf.get_loc_expr().assign(IdentifierExpr(param.idf.name)))

    def get_circuit_output_for_private_expression(self, expr: Expression, new_privacy: PrivacyLabelExpr) -> LocationExpr:
        """
        Corresponds to out() from paper
        :param expr: The expression which should be evaluated privately
        :param new_privacy: The circuit output should be encrypted for this owner (or plain if 'all')
        :return: Location expression which references the encrypted circuit result
        """
        ecode = expr.code()
        with CircIndentBlockBuilder(f'[{expr.statement.function.name}]: {ecode}', self._phi):
            plain_result_idf, priv_expr = self._evaluate_private_expression(expr)

            if new_privacy.is_all_expr():
                new_out_param = self._out_name_factory.get_new_idf(expr.annotated_type.type_name, priv_expr)
                self._phi.append(EqConstraint(plain_result_idf, new_out_param))
                out_var = new_out_param.get_loc_expr().implicitly_converted(expr.annotated_type.type_name)
            else:
                new_out_param = self._out_name_factory.get_new_idf(TypeName.cipher_type(), EncryptionExpression(priv_expr, new_privacy))
                self._ensure_encryption(plain_result_idf, new_privacy, new_out_param, False)
                out_var = new_out_param.get_loc_expr()

        self._phi.append(CircComment(f'{new_out_param.name} = {ecode}\n'))

        expr.statement.pre_statements.append(CircuitComputationStatement(new_out_param))
        return out_var

    def add_to_circuit_inputs(self, loc_expr: LocationExpr) -> LocationExpr:
        """
        Corresponds to in() from paper
        :param loc_expr: Location (contract variable) which should be made available inside the circuit
        :return: Location expression which references the (decrypted if necessary) input value
        """
        privacy = Expression.me_expr() if loc_expr.annotated_type.is_private() else Expression.all_expr()

        expr_text = loc_expr.code()
        input_expr = self._expr_trafo.visit(loc_expr)
        if privacy.is_all_expr():
            input_idf = self._in_name_factory.get_new_idf(loc_expr.annotated_type.type_name)
            locally_decrypted_idf = input_idf
        else:
            locally_decrypted_idf = self._secret_input_name_factory.get_new_idf(loc_expr.annotated_type.type_name)
            input_idf = self._in_name_factory.get_new_idf(TypeName.cipher_type(), IdentifierExpr(locally_decrypted_idf))
            self._ensure_encryption(locally_decrypted_idf, Expression.me_expr(), input_idf, False)

        self._phi.append(CircComment(f'{input_idf.name} (dec: {locally_decrypted_idf.name}) = {expr_text}'))
        loc_expr.statement.pre_statements.append(CircuitInputStatement(input_idf.get_loc_expr(), input_expr))
        return locally_decrypted_idf.get_loc_expr()

    # For inlining
    # prepend:
    # 1. assign args to temporary variables
    # 2. include original function body with replaced parameter idfs
    # 3. assign return value to temporary var
    # return temp ret var

    def inline_function(self, ast: FunctionCallExpr, fdef: FunctionDefinition):
        with InlineRemap(self):
            calltext = f'INLINED {ast.code()}'

            inlined_code = IndentBlock(calltext, [])

            for param, arg in zip(fdef.parameters, ast.args):
                inlined_code.statements.append(self.create_temporary_variable(param.idf.name, param.annotated_type, self._expr_trafo.visit(arg)))
            inlined_stmts = fdef.original_body.clone().statements
            for stmt in inlined_stmts:
                trafo_stmt = self._inline_stmt_trafo.visit(stmt)
                inlined_code.statements += trafo_stmt.pre_statements + [trafo_stmt]
                trafo_stmt.pre_statements = []
            inlined_code.statements.append(BlankLine())
            ast.statement.pre_statements.append(inlined_code)

            if fdef.return_parameters:
                assert len(fdef.return_parameters) == 1
                ret_t = fdef.return_parameters[0].annotated_type
                ret = ast.replaced_with(self._inline_var_remap[cfg.return_var_name].get_loc_expr()).as_type(ret_t)
            else:
                ret = None
        return ret

    def inline_circuit_function(self, ast: FunctionCallExpr, fdef: FunctionDefinition):
        with InlineRemap(self):
            with CircIndentBlockBuilder(f'INLINED {ast.code()}', self._phi):
                for param, arg in zip(fdef.parameters, ast.args):
                    self.create_temporary_circuit_variable(Identifier(param.idf.name).decl_var(param.annotated_type, arg))
                inlined_stmts = fdef.original_body.clone().statements
                for stmt in inlined_stmts:
                    self._circ_trafo.visit(stmt)
                    ast.statement.pre_statements += stmt.pre_statements
                ret_var_idf = self._inline_var_remap[cfg.return_var_name]
                ret = IdentifierExpr(ret_var_idf.clone()).as_type(ret_var_idf.t)
        return ret

    def get_remapped_idf(self, idf: IdentifierExpr) -> LocationExpr:
        if idf.idf.name in self._inline_var_remap:
            return idf.replaced_with(self._inline_var_remap[idf.idf.name].get_loc_expr()).as_type(idf.annotated_type)
        else:
            return idf

    def create_temporary_variable(self, original_idf: str, t: AnnotatedTypeName, expr: Optional[Expression]) -> AssignmentStatement:
        base_name = self._local_var_name_factory.get_new_name(t.type_name, False)
        tmp_var = self._local_var_name_factory.add_idf(f'{base_name}_{original_idf}', t.type_name)
        self._inline_var_remap[original_idf] = tmp_var
        ret = IdentifierExpr(cfg.zk_data_var_name).dot(tmp_var).as_type(t).assign(expr)
        return ret

    def create_temporary_circuit_variable(self, ast: VariableDeclarationStatement):
        tmp_var, priv_expr = self._evaluate_private_expression(ast.expr)
        self._inline_var_remap[ast.variable_declaration.idf.name] = tmp_var

    def add_assignment_to_circuit(self, ast: AssignmentStatement):
        lhs = self._circ_trafo.visit(ast.lhs)
        rhs = self._circ_trafo.visit(ast.rhs)
        assert isinstance(lhs, LocationExpr)
        self._phi.append(CircAssignment(lhs, rhs))

    def _evaluate_private_expression(self, expr: Expression):
        priv_expr = self._circ_trafo.visit(expr)
        sec_circ_var_idf = self._circ_temp_name_factory.get_new_idf(expr.annotated_type.type_name, priv_expr)
        stmt = TempVarDecl(sec_circ_var_idf, priv_expr)
        self.phi.append(stmt)
        return sec_circ_var_idf, priv_expr

    def _ensure_encryption(self, plain: HybridArgumentIdf, new_privacy: PrivacyLabelExpr, cipher: HybridArgumentIdf, is_param: bool):
        rnd = self._secret_input_name_factory.add_idf(f'{plain.name if is_param else cipher.name}_R', TypeName.rnd_type())
        pk = self._request_public_key(new_privacy)
        self._phi.append(EncConstraint(plain, rnd, pk, cipher))

    def _request_public_key(self, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        pname = privacy.idf.name
        if pname in self._pk_for_label:
            return self._pk_for_label[pname].lhs.member
        else:
            idf = self._in_name_factory.get_new_idf(TypeName.key_type())
            pki = IdentifierExpr(get_contract_instance_idf(cfg.pki_contract_name))
            self._pk_for_label[pname] = idf.get_loc_expr().assign(pki.call('getPk', [self._expr_trafo.visit(privacy)]))
            return idf


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
        self.prev = self.c._inline_var_remap
        self.c._inline_var_remap = {}
        self.c._inline_var_remap.update(self.prev)

    def __exit__(self, t, value, traceback):
        self._inline_var_remap = self.prev
