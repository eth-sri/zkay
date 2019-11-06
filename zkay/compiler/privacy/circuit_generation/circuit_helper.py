from typing import List, Dict, Optional, Tuple, Callable

import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircuitStatement, EncConstraint, ExpressionToLocAssignment, \
    EqConstraint
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.zkay_ast.ast import Expression, IdentifierExpr, PrivacyLabelExpr, \
    LocationExpr, TypeName, AssignmentStatement, UserDefinedTypeName, ConstructorOrFunctionDefinition, Parameter, \
    HybridArgumentIdf, EncryptionExpression


class NameFactory:
    def __init__(self, base_name: str, is_private: bool):
        self.base_name = base_name
        self.is_private = is_private
        self.count = 0
        self.size = 0
        self.idfs = []

    def get_new_idf(self, t: TypeName, priv_expr: Optional[Expression] = None) -> HybridArgumentIdf:
        if t == TypeName.key_type():
            postfix = 'key'
        elif t == TypeName.cipher_type():
            postfix = 'cipher'
        else:
            postfix = 'plain'
        name = f'{self.base_name}{self.count}_{postfix}'

        idf = HybridArgumentIdf(name, t, self.is_private, priv_expr)
        self.count += 1
        self.size += t.size_in_uints
        self.idfs.append(idf)
        return idf

    def add_idf(self, name: str, t: TypeName):
        idf = HybridArgumentIdf(name, t, self.is_private)
        self.count += 1
        self.size += t.size_in_uints
        self.idfs.append(idf)
        return idf


class CircuitHelper:
    def __init__(self, fct: ConstructorOrFunctionDefinition,
                 expr_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor],
                 circ_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor]):
        super().__init__()
        self.fct = fct
        self._expr_trafo: AstTransformerVisitor = expr_trafo_constructor(self)
        self._circ_trafo: AstTransformerVisitor = circ_trafo_constructor(self)

        self.has_return_var = False
        self.verifier_contract_filename: Optional[str] = None
        self.verifier_contract_type: Optional[UserDefinedTypeName] = None

        self._phi: List[CircuitStatement] = []
        """ List of proof circuit statements (assertions and assignments) """

        # Private inputs
        self._secret_input_name_factory = NameFactory('secret', is_private=True)
        # Circuit internal
        self._local_expr_name_factory = NameFactory('tmp', is_private=True)

        # Public inputs
        self._out_name_factory = NameFactory(cfg.zk_out_name, is_private=False)
        self._in_name_factory = NameFactory(cfg.zk_in_name, is_private=False)

        # Public contract elements
        self._pk_for_label: Dict[str, AssignmentStatement] = {}
        self._param_to_in_assignments: List[AssignmentStatement] = []

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
        return self.has_in_args or self.has_out_args or self._secret_input_name_factory.count

    def encrypt_parameter(self, param: Parameter):
        plain_idf = self._secret_input_name_factory.add_idf(param.idf.name, param.annotated_type.type_name)
        cipher_idf = self._in_name_factory.get_new_idf(TypeName.cipher_type())
        self._ensure_encryption(plain_idf, Expression.me_expr(), cipher_idf, True)
        self.param_to_in_assignments.append(cipher_idf.get_loc_expr().assign(IdentifierExpr(param.idf.name)))

    def move_out(self, expr: Expression, new_privacy: PrivacyLabelExpr):
        plain_result_idf, priv_expr = self._evaluate_private_expression(expr)

        if new_privacy.is_all_expr():
            new_out_param = self._out_name_factory.get_new_idf(expr.annotated_type.type_name, priv_expr)
            self._phi.append(EqConstraint(plain_result_idf, new_out_param))
            out_var = new_out_param.get_loc_expr().implicitly_converted(expr.annotated_type.type_name)
        else:
            new_out_param = self._out_name_factory.get_new_idf(TypeName.cipher_type(), EncryptionExpression(priv_expr, new_privacy))
            self._ensure_encryption(plain_result_idf, new_privacy, new_out_param, False)
            out_var = new_out_param.get_loc_expr()

        expr.statement.out_refs.append(new_out_param)
        return out_var

    def move_in(self, loc_expr: LocationExpr, privacy: PrivacyLabelExpr):
        input_expr = self._expr_trafo.visit(loc_expr)
        if privacy.is_all_expr():
            input_idf = self._in_name_factory.get_new_idf(loc_expr.annotated_type.type_name)
            locally_decrypted_idf = input_idf
        else:
            locally_decrypted_idf = self._secret_input_name_factory.get_new_idf(loc_expr.annotated_type.type_name)
            input_idf = self._in_name_factory.get_new_idf(TypeName.cipher_type(), IdentifierExpr(locally_decrypted_idf))
            self._ensure_encryption(locally_decrypted_idf, Expression.me_expr(), input_idf, False)

        loc_expr.statement.in_assignments.append(input_idf.get_loc_expr().assign(input_expr))
        return locally_decrypted_idf.get_loc_expr()

    def _evaluate_private_expression(self, expr: Expression):
        priv_expr = self._circ_trafo.visit(expr)
        sec_circ_var_idf = self._local_expr_name_factory.get_new_idf(expr.annotated_type.type_name)
        stmt = ExpressionToLocAssignment(sec_circ_var_idf, priv_expr)
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
