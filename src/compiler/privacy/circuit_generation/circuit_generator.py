from abc import ABCMeta, abstractmethod
from typing import List, Dict

from compiler.privacy.circuit_generation.proving_scheme import ProvingScheme, VerifyingKey
from compiler.privacy.transformer.zkay_transformer import ZkayCircuitTransformer, ZkayExpressionTransformer
from zkay_ast.ast import Expression, Parameter, Statement, IdentifierExpr, AnnotatedTypeName, \
    Identifier, VariableDeclarationStatement, VariableDeclaration, FunctionCallExpr, MemberAccessExpr, PrivacyLabelExpr, LocationExpr, \
    TypeName


class HybridArgumentIdf(Identifier):
    def __init__(self, name: str, t: TypeName):
        super().__init__(name)
        self.t = t


class DecryptLocallyIdf(HybridArgumentIdf):
    def __init__(self, name: str, t: TypeName, idf: HybridArgumentIdf):
        super().__init__(name, t)
        self.idf = idf


class EncParamIdf(HybridArgumentIdf):
    pass


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

    def get_new_idf(self, t: TypeName) -> HybridArgumentIdf:
        idf = HybridArgumentIdf(f'{self.base_name}_{self.count}', t)
        self.count += 1
        return idf


class CircuitHelper:
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

        self.local_expr_name_factory = NameFactory('__secret_')

        # Public contract elements
        self.pk_name_factory = NameFactory('__pk_')
        self.pk_for_label: Dict[str, VariableDeclarationStatement] = {}

        self.temp_name_factory = NameFactory('__in_')
        self.temp_vars: Dict[Statement, List[VariableDeclarationStatement]] = {}

        self.param_name_factory = NameFactory('__out_')
        self.additional_params: List[Parameter] = []

    @staticmethod
    def get_type(expr: Expression, privacy: PrivacyLabelExpr) -> TypeName:
        return expr.annotated_type.type_name if privacy.is_all_expr() else TypeName.cipher_type()

    def request_public_key(self, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        pname = privacy.idf.name
        if pname in self.pk_for_label:
            return self.pk_for_label[pname].variable_declaration.idf
        else:
            idf = self.pk_name_factory.get_new_idf(TypeName.key_type())
            pki_idf = self.zkay_trafo.used_contracts[0].state_variable_idf
            assert pki_idf
            self.pk_for_label[pname] = VariableDeclarationStatement(
                VariableDeclaration(
                    [], AnnotatedTypeName.key_type(), idf,
                ),
                FunctionCallExpr(MemberAccessExpr(IdentifierExpr(pki_idf), Identifier('getPk')), [privacy])
            )
            return idf

    def add_param(self, expr: Expression, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        t = self.get_type(expr, privacy)
        idf = self.param_name_factory.get_new_idf(t)
        self.additional_params.append(Parameter(
            [], AnnotatedTypeName(t, None), idf, None # TODO need to specify storage loc?
        ))
        return idf

    def add_temp_var(self, expr: Expression, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        te = ZkayExpressionTransformer(self.zkay_trafo).visit(expr)
        te_t = self.get_type(expr, privacy)
        idf = self.temp_name_factory.get_new_idf(te_t)
        stmt = VariableDeclarationStatement(VariableDeclaration([], AnnotatedTypeName(te_t, None), idf), te)
        if expr.statement in self.temp_vars:
            self.temp_vars[expr.statement].append(stmt)
        else:
            self.temp_vars[expr.statement] = [stmt]
        return idf

    def ensure_encryption(self, plain: HybridArgumentIdf, new_privacy: PrivacyLabelExpr, cipher: HybridArgumentIdf):
        rnd = HybridArgumentIdf(f'{cipher.name}_R', TypeName.rnd_type())

        self.s.append(rnd)

        pk = self.request_public_key(new_privacy)
        self.p.append(pk)

        self.p.append(cipher)
        self.phi.append(EncConstraint(plain, rnd, pk, cipher))

    def move_out(self, expr: Expression, new_privacy: PrivacyLabelExpr):
        new_param = self.add_param(expr, new_privacy)

        rhs_expr = ZkayCircuitTransformer(self.zkay_trafo).visit(expr)
        sec_circ_var_idf = self.local_expr_name_factory.get_new_idf(rhs_expr.annotated_type.type_name)
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
            new_idf_name = self.local_expr_name_factory.get_new_idf(TypeName.void_type()).name
            dec_loc_idf = DecryptLocallyIdf(new_idf_name, loc_expr.annotated_type.type_name, new_var)
            self.s.append(dec_loc_idf)
            self.ensure_encryption(dec_loc_idf, Expression.me_expr(), new_var)

        return loc_expr.replaced_with(IdentifierExpr(new_var))


class CircuitGenerator(metaclass=ABCMeta):
    def __init__(self, circuits: List[CircuitHelper], proving_scheme: ProvingScheme):
        self.circuits = circuits
        self.proving_scheme = proving_scheme

    def generate_circuits(self):
        # Generate code which is needed to issue a transaction for this function (offchain computations)
        self._generate_offchain_code()

        # Generate proof circuit, keys and verification contract
        self._generate_zkcircuit()
        self._generate_keys()

        vk = self._parse_verification_key()
        vcontract_str = self.proving_scheme.generate_verification_contract(vk, 0)

    def _generate_offchain_code(self):
        # Generate python code corresponding to the off-chain computations for the circuit
        pass

    @abstractmethod
    def _parse_verification_key(self) -> VerifyingKey:
        pass

    @abstractmethod
    def _generate_zkcircuit(self):
        pass

    @abstractmethod
    def _generate_keys(self):
        pass