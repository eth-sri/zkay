from abc import ABCMeta, abstractmethod
from typing import Optional, List, Dict

from compiler.privacy.circuit_generation.proving_scheme import ProvingScheme, VerifyingKey
from compiler.privacy.transformer.zkay_transformer import ZkayCircuitTransformer, ZkayExpressionTransformer, DecryptionExpr
from zkay_ast.ast import Expression, Parameter, Statement, IdentifierExpr, AnnotatedTypeName, \
    Identifier, VariableDeclarationStatement, VariableDeclaration, FunctionCallExpr, MemberAccessExpr, PrivacyLabelExpr, LocationExpr


class HybridArgumentIdf(Identifier):
    pass


class DecryptLocallyIdf(HybridArgumentIdf):
    def __init__(self, name: str, idf: HybridArgumentIdf):
        super().__init__(name)
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
        pass


class EqConstraint(CircuitStatement):
    def __init__(self, expr: HybridArgumentIdf, val: HybridArgumentIdf):
        pass


class NameFactory:
    def __init__(self, base_name: str):
        self.base_name = base_name
        self.count = 0

    def get_new_idf(self) -> HybridArgumentIdf:
        idf = HybridArgumentIdf(f'{self.base_name}_{self.count}')
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
    def get_type(expr: Expression, privacy: PrivacyLabelExpr):
        return AnnotatedTypeName(expr.annotated_type.type_name, None) if privacy.is_all_expr() else AnnotatedTypeName.cipher_type()

    def request_public_key(self, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        pname = privacy.idf.name
        if pname in self.pk_for_label:
            return self.pk_for_label[pname].variable_declaration.idf
        else:
            idf = self.pk_name_factory.get_new_idf()
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
        idf = self.param_name_factory.get_new_idf()
        self.additional_params.append(Parameter(
            [], self.get_type(expr, privacy), idf, None # TODO need to specify storage loc?
        ))
        return idf

    def add_temp_var(self, expr: Expression, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        idf = self.temp_name_factory.get_new_idf()
        te = ZkayExpressionTransformer(self.zkay_trafo).visit(expr)
        stmt = VariableDeclarationStatement(VariableDeclaration([], self.get_type(expr, privacy), idf), te)
        if expr.statement in self.temp_vars:
            self.temp_vars[expr.statement].append(stmt)
        else:
            self.temp_vars[expr.statement] = [stmt]
        return idf

    def ensure_encryption(self, plain: HybridArgumentIdf, new_privacy: PrivacyLabelExpr, cipher: HybridArgumentIdf):
        rnd = HybridArgumentIdf(f'{cipher.name}_R')

        self.s.append(rnd)

        pk = self.request_public_key(new_privacy)
        self.p.append(pk)

        self.p.append(cipher)
        self.phi.append(EncConstraint(plain, rnd, pk, cipher))

    def move_out(self, expr: Expression, new_privacy: PrivacyLabelExpr):
        new_param = self.add_param(expr, new_privacy)

        sec_circ_var_idf = self.local_expr_name_factory.get_new_idf()
        self.phi.append(ExpressionToLocAssignment(sec_circ_var_idf, ZkayCircuitTransformer(self.zkay_trafo).visit(expr)))

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
            dec_loc_idf = DecryptLocallyIdf(self.local_expr_name_factory.get_new_idf().name, new_var)
            self.s.append(dec_loc_idf)
            self.ensure_encryption(dec_loc_idf, Expression.me_expr(), new_var)

        return loc_expr.replaced_with(IdentifierExpr(new_var))


class CircuitGenerator(metaclass=ABCMeta):
    def __init__(self, circuit: CircuitHelper, proving_scheme: ProvingScheme):
        self.circuit = circuit
        self.proving_scheme = proving_scheme

    def generate_circuit(self):
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