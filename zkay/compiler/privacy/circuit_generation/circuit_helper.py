from typing import List, Dict, Optional, Tuple, Callable

import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircuitStatement, EncConstraint, TempVarDecl, \
    EqConstraint, CircAssignment, CircComment, CircIndentBlock
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.zkay_ast.ast import Expression, IdentifierExpr, PrivacyLabelExpr, \
    LocationExpr, TypeName, AssignmentStatement, UserDefinedTypeName, ConstructorOrFunctionDefinition, Parameter, \
    HybridArgumentIdf, EncryptionExpression, FunctionCallExpr, FunctionDefinition, VariableDeclarationStatement, \
    Identifier, \
    AnnotatedTypeName, Statement, IndentBlock, HybridArgType, Comment, CircuitInputStatement, CircuitComputationStatement


class BaseNameFactory:
    def __init__(self, base_name: str):
        self.base_name = base_name
        self.count = 0

    def get_new_name(self, t: TypeName, inc=True) -> str:
        if t == TypeName.key_type():
            postfix = 'key'
        elif t == TypeName.cipher_type():
            postfix = 'cipher'
        else:
            postfix = 'plain'
        name = f'{self.base_name}{self.count}_{postfix}'
        if inc:
            self.count += 1
        return name


class NameFactory(BaseNameFactory):
    def __init__(self, base_name: str, arg_type: HybridArgType):
        super().__init__(base_name)
        self.arg_type = arg_type
        self.size = 0
        self.idfs = []

    def get_new_idf(self, t: TypeName, priv_expr: Optional[Expression] = None) -> HybridArgumentIdf:
        name = self.get_new_name(t)
        idf = HybridArgumentIdf(name, t, self.arg_type, priv_expr)
        self.size += t.size_in_uints
        self.idfs.append(idf)
        return idf

    def add_idf(self, name: str, t: TypeName):
        idf = HybridArgumentIdf(name, t, self.arg_type)
        self.count += 1
        self.size += t.size_in_uints
        self.idfs.append(idf)
        return idf


class CircuitHelper:
    def __init__(self, fct: ConstructorOrFunctionDefinition,
                 inline_stmt_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 expr_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 circ_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor]):
        super().__init__()
        self.fct = fct
        self._inline_stmt_trafo: AstTransformerVisitor = inline_stmt_trafo_constructor(self)
        self._current_pre_stmts: Optional[Statement] = None
        self._expr_trafo: AstTransformerVisitor = expr_trafo_constructor(self)
        self._circ_trafo: AstTransformerVisitor = circ_trafo_constructor(self)

        self.has_return_var = False
        self.verifier_contract_filename: Optional[str] = None
        self.verifier_contract_type: Optional[UserDefinedTypeName] = None

        self._phi: List[CircuitStatement] = []
        """ List of proof circuit statements (assertions and assignments) """

        # Local variables outside circuit
        self._local_var_name_factory = NameFactory('_zk_tmp', arg_type=HybridArgType.PUB_CONTRACT_VAL)

        # Private inputs
        self._secret_input_name_factory = NameFactory('secret', arg_type=HybridArgType.PRIV_CIRCUIT_VAL)
        # Circuit internal
        self._circ_temp_name_factory = NameFactory('tmp', arg_type=HybridArgType.PRIV_CIRCUIT_VAL)

        # Public inputs
        self._out_name_factory = NameFactory(cfg.zk_out_name, arg_type=HybridArgType.PUB_CIRCUIT_ARG)
        self._in_name_factory = NameFactory(cfg.zk_in_name, arg_type=HybridArgType.PUB_CIRCUIT_ARG)

        # Public contract elements
        self._pk_for_label: Dict[str, AssignmentStatement] = {}
        self._param_to_in_assignments: List[AssignmentStatement] = []

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
    def public_out_array(self) -> Tuple[str, int]:
        return self._out_name_factory.base_name, self._out_name_factory.size

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
    def secret_param_names(self) -> List[str]:
        return [idf.name for idf in self._secret_input_name_factory.idfs]

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

    def encrypt_parameter(self, param: Parameter):
        plain_idf = self._secret_input_name_factory.add_idf(param.idf.name, param.annotated_type.type_name)
        cipher_idf = self._in_name_factory.get_new_idf(TypeName.cipher_type())
        self._ensure_encryption(plain_idf, Expression.me_expr(), cipher_idf, True)
        self.param_to_in_assignments.append(cipher_idf.get_loc_expr().assign(IdentifierExpr(param.idf.name)))

    def move_out(self, expr: Expression, new_privacy: PrivacyLabelExpr):
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

    def move_in(self, loc_expr: LocationExpr, privacy: PrivacyLabelExpr):
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

    def inline_function(self, ast: FunctionCallExpr, fdef: FunctionDefinition):
        prevmap = self._inline_var_remap
        self._inline_var_remap = {}
        self._inline_var_remap.update(prevmap)

        calltext = f'INLINED {ast.code()}'

        inlined_code = IndentBlock(calltext, [])

        for param, arg in zip(fdef.parameters, ast.args):
            inlined_code.statements.append(self.create_temporary_variable(param.idf.name, param.annotated_type, self._expr_trafo.visit(arg)))
        inlined_stmts = fdef.original_body.clone().statements
        for stmt in inlined_stmts:
            trafo_stmt = self._inline_stmt_trafo.visit(stmt)
            inlined_code.statements += trafo_stmt.pre_statements + [trafo_stmt]
            trafo_stmt.pre_statements = []
        inlined_code.statements.append(Comment())
        ast.statement.pre_statements.append(inlined_code)

        if fdef.return_parameters:
            assert len(fdef.return_parameters) == 1
            ret = ast.replaced_with(self._inline_var_remap[cfg.return_var_name].get_loc_expr()).as_type(fdef.return_parameters[0].annotated_type)
        else:
            ret = None

        self._inline_var_remap = prevmap

        return ret

    def inline_circuit_function(self, ast: FunctionCallExpr, fdef: FunctionDefinition):
        # prepend this to the current circuit statement:
        # 1. assign args to temporary variables
        # 2. include original function body with replaced parameter idfs
        # 3. assign return value to temporary var
        # return temp ret var

        prevmap = self._inline_var_remap
        self._inline_var_remap = {}
        self._inline_var_remap.update(prevmap)

        with CircIndentBlockBuilder(f'INLINED {ast.code()}', self._phi):
            for param, arg in zip(fdef.parameters, ast.args):
                self.create_circuit_temp_var_decl(Identifier(param.idf.name).decl_var(param.annotated_type, arg))
            inlined_stmts = fdef.original_body.clone().statements
            for stmt in inlined_stmts:
                self._circ_trafo.visit(stmt)
                ast.statement.pre_statements += stmt.pre_statements
            ret = IdentifierExpr(self._inline_var_remap[cfg.return_var_name].clone(), AnnotatedTypeName(self._inline_var_remap[cfg.return_var_name].t))
        self._inline_var_remap = prevmap
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

    def create_circuit_temp_var_decl(self, ast: VariableDeclarationStatement):
        tmp_var, priv_expr = self._evaluate_private_expression(ast.expr)
        self._inline_var_remap[ast.variable_declaration.idf.name] = tmp_var

    def create_assignment(self, ast: AssignmentStatement):
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
