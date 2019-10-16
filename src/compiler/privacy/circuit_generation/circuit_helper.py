from typing import List, Dict, Optional, Tuple

from compiler.privacy.used_contract import UsedContract
from zkay_ast.ast import Expression, Statement, IdentifierExpr, Identifier, FunctionCallExpr, MemberAccessExpr, PrivacyLabelExpr, \
    LocationExpr, \
    TypeName, AssignmentStatement


class HybridArgumentIdf(Identifier):
    def __init__(self, name: str, offset: Optional[int], t: TypeName):
        super().__init__(name)
        self.t = t
        self.offset = offset


class DecryptLocallyIdf(HybridArgumentIdf):
    def __init__(self, name: str, t: TypeName, idf: HybridArgumentIdf):
        super().__init__(name, None, t)
        self.idf = idf


class EncParamIdf(HybridArgumentIdf):
    def __init__(self, name: str, t: TypeName):
        super().__init__(name, None, t)


class CircuitStatement:
    pass


class ExpressionToLocAssignment(CircuitStatement):
    def __init__(self, lhs: HybridArgumentIdf, expr: Expression):
        self.lhs = lhs
        self.expr = expr


class EncConstraint(CircuitStatement):
    def __init__(self, plain: HybridArgumentIdf, rnd: HybridArgumentIdf, pk: HybridArgumentIdf, cipher: HybridArgumentIdf):
        self.plain = plain
        self.rnd = rnd
        self.pk = pk
        self.cipher = cipher


class EqConstraint(CircuitStatement):
    def __init__(self, expr: HybridArgumentIdf, val: HybridArgumentIdf):
        self.expr = expr
        self.val = val


class NameFactory:
    def __init__(self, base_name: str):
        self.base_name = base_name
        self.count = 0
        self.fstring = '{}_{}'

    def get_new_idf(self, t: TypeName) -> HybridArgumentIdf:
        idf = HybridArgumentIdf(self.fstring.format(self.base_name, self.count), self.count, t)
        self.count += 1
        return idf


class ArrayBasedNameFactory(NameFactory):
    def __init__(self, base_name: str):
        super().__init__(base_name)
        self.fstring = '{}[{}]'


class CircuitHelper:
    param_base_name = '__out'
    temp_base_name = '__in'

    def __init__(self, zkay_trafo):
        super().__init__()
        self.zkay_trafo = zkay_trafo

        # Circuit elements
        self.p: List[HybridArgumentIdf] = []
        """Public arguments for proof circuit"""

        self.s: List[HybridArgumentIdf] = []
        """Secret argument for proof circuit"""

        self.phi: List[CircuitStatement] = []
        """List of constraints which are checked by proof circuit"""

        self.verifier_contract: Optional[UsedContract] = None

        self.secret_input_name_factory = NameFactory('__secret_')
        self.local_expr_name_factory = NameFactory('__tmp_')

        self.param_name_factory = ArrayBasedNameFactory(CircuitHelper.param_base_name)
        self.temp_name_factory = ArrayBasedNameFactory(CircuitHelper.temp_base_name)

        # Public contract elements
        self.pk_for_label: Dict[str, AssignmentStatement] = {}
        self.temp_vars: Dict[Statement, Tuple[str, List[AssignmentStatement]]] = {}

    @staticmethod
    def get_type(expr: Expression, privacy: PrivacyLabelExpr) -> TypeName:
        return expr.annotated_type.type_name if privacy.is_all_expr() else TypeName.cipher_type()

    def request_public_key(self, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        pname = privacy.idf.name
        if pname in self.pk_for_label:
            return self.pk_for_label[pname].lhs.idf
        else:
            idf = self.temp_name_factory.get_new_idf(TypeName.key_type())
            pki_idf = self.zkay_trafo.used_contracts[0].state_variable_idf
            assert pki_idf
            self.pk_for_label[pname] = AssignmentStatement(
                IdentifierExpr(idf), FunctionCallExpr(MemberAccessExpr(IdentifierExpr(pki_idf), Identifier('getPk')),
                                                      [self.zkay_trafo.visit(privacy)])
            )
            return idf

    def add_param(self, expr: Expression, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        t = self.get_type(expr, privacy)
        idf = self.param_name_factory.get_new_idf(t)
        return idf

    def add_temp_var(self, expr: Expression, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        from compiler.privacy.transformer.zkay_transformer import ZkayExpressionTransformer
        te = ZkayExpressionTransformer(self.zkay_trafo).visit(expr)
        te_t = self.get_type(expr, privacy)
        idf = self.temp_name_factory.get_new_idf(te_t)
        stmt = AssignmentStatement(IdentifierExpr(idf), te)
        assert expr.statement is not None
        if expr.statement in self.temp_vars:
            self.temp_vars[expr.statement][1].append(stmt)
        else:
            self.temp_vars[expr.statement] = (expr.statement.code(), [stmt])
        return idf

    def ensure_encryption(self, plain: HybridArgumentIdf, new_privacy: PrivacyLabelExpr, cipher: HybridArgumentIdf):
        rnd = HybridArgumentIdf(f'{cipher.name}_R', None, TypeName.rnd_type())

        if isinstance(plain, EncParamIdf) or isinstance(plain, DecryptLocallyIdf):
            self.s.append(plain)

        self.s.append(rnd)

        pk = self.request_public_key(new_privacy)
        self.p.append(pk)

        self.p.append(cipher)
        self.phi.append(EncConstraint(plain, rnd, pk, cipher))

    def move_out(self, expr: Expression, new_privacy: PrivacyLabelExpr):
        new_param = self.add_param(expr, new_privacy)

        from compiler.privacy.transformer.zkay_transformer import ZkayCircuitTransformer
        rhs_expr = ZkayCircuitTransformer(self.zkay_trafo).visit(expr)
        sec_circ_var_idf = self.local_expr_name_factory.get_new_idf(expr.annotated_type.type_name)
        self.phi.append(ExpressionToLocAssignment(sec_circ_var_idf, rhs_expr))

        if not new_privacy.is_all_expr():
            self.ensure_encryption(sec_circ_var_idf, new_privacy, new_param)
        else:
            self.p.append(new_param)
            self.phi.append(EqConstraint(sec_circ_var_idf, new_param))

        return expr.replaced_with(IdentifierExpr(new_param))

    def move_in(self, loc_expr: LocationExpr, privacy: PrivacyLabelExpr):
        new_var = self.add_temp_var(loc_expr, privacy)
        self.p.append(new_var)

        if privacy.is_me_expr():
            # Instead of secret key, decrypt outside proof circuit (but locally), add plain value as secret param
            #  and prove encryption (because its not feasible to decrypt inside proof circuit)
            new_idf_name = self.secret_input_name_factory.get_new_idf(TypeName.void_type()).name
            dec_loc_idf = DecryptLocallyIdf(new_idf_name, loc_expr.annotated_type.type_name, new_var)
            self.ensure_encryption(dec_loc_idf, Expression.me_expr(), new_var)

        return loc_expr.replaced_with(IdentifierExpr(new_var))

