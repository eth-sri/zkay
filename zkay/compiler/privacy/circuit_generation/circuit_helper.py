from copy import deepcopy
from typing import List, Dict, Optional, Tuple, Callable

from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.privacy.used_contract import UsedContract
from zkay.zkay_ast.ast import Expression, Statement, IdentifierExpr, Identifier, FunctionCallExpr, MemberAccessExpr, PrivacyLabelExpr, \
    LocationExpr, \
    TypeName, AssignmentStatement, UserDefinedTypeName, AnnotatedTypeName, ConstructorOrFunctionDefinition, IndexExpr, NumberLiteralExpr


class HybridArgumentIdf(Identifier):
    def __init__(self, name: str, offset: Optional[int], t: TypeName):
        super().__init__(name)
        self.t = t # transformed type of this idf
        self.offset = offset
        self.corresponding_expression: Optional[IdfValue] = None
        self.corresponding_plaintext_circuit_input: Optional[HybridArgumentIdf] = None

    def get_loc_expr(self, t: Optional[AnnotatedTypeName] = None):
        if self.offset is None:
            expr = IdentifierExpr(self)
        else:
            expr = IndexExpr(IdentifierExpr(self), NumberLiteralExpr(self.offset))
        if t is not None:
            expr.annotated_type = t
        return expr

    def get_flat_name(self):
        if self.offset is None:
            return self.name
        else:
            return f'{self.name}{self.offset}'


class EncParamIdf(HybridArgumentIdf):
    def __init__(self, name: str, t: TypeName):
        super().__init__(name, None, t)


class CircuitStatement:
    pass


class ExpressionToLocAssignment(CircuitStatement):
    def __init__(self, lhs: HybridArgumentIdf, expr: Expression):
        self.lhs = lhs
        self.expr = expr


class IdfValue:
    def __init__(self, privacy: Expression, val: Expression):
        self.privacy = privacy
        self.val = val


class EncConstraint(CircuitStatement):
    def __init__(self, plain: HybridArgumentIdf, rnd: HybridArgumentIdf, pk: HybridArgumentIdf, cipher: HybridArgumentIdf):
        self.plain = plain
        self.rnd = rnd
        self.pk = pk
        self.cipher = cipher


class EqConstraint(CircuitStatement):
    def __init__(self, tgt: HybridArgumentIdf, val: HybridArgumentIdf):
        self.tgt = tgt
        self.val = val


class NameFactory:
    def __init__(self, base_name: str):
        self.base_name = base_name
        self.count = 0

    def get_new_idf(self, t: TypeName) -> HybridArgumentIdf:
        idf = HybridArgumentIdf(f'{self.base_name}_{self.count}', None, t)
        self.count += 1
        return idf


class ArrayBasedNameFactory(NameFactory):
    def get_new_idf(self, t: TypeName) -> HybridArgumentIdf:
        idf = HybridArgumentIdf(f'{self.base_name}', self.count, t)
        self.count += 1
        return idf


class CircuitHelper:
    out_base_name = 'out__'
    in_base_name = 'in__'

    def __init__(self, fct: ConstructorOrFunctionDefinition,
                 used_contracts: List[UsedContract], expr_trafo_constructor: Callable[['CircuitHelper'], AstTransformerVisitor]):
        super().__init__()
        self.fct = fct
        self.used_contracts = used_contracts
        self.expr_trafo: AstTransformerVisitor = expr_trafo_constructor(self)
        self.enc_param_check_stmts: List[AssignmentStatement] = []
        self.return_var: Optional[Identifier] = None
        self.verifier_contract: Optional[UsedContract] = None

        # Circuit elements
        self.p: List[HybridArgumentIdf] = []
        """ Public arguments for proof circuit """

        self.s: List[HybridArgumentIdf] = []
        """ Secret argument for proof circuit """

        self.phi: List[CircuitStatement] = []
        """ List of proof circuit statements (assertions and assignments) """

        self.secret_input_name_factory = NameFactory('secret_')
        self.local_expr_name_factory = NameFactory('tmp_')

        self.out_name_factory = ArrayBasedNameFactory(CircuitHelper.out_base_name)
        self.in_name_factory = ArrayBasedNameFactory(CircuitHelper.in_base_name)

        # Public contract elements
        self.pk_for_label: Dict[str, AssignmentStatement] = {}
        self.old_code_and_temp_var_decls_for_stmt: Dict[Statement, Tuple[str, List[AssignmentStatement]]] = {}

    def get_circuit_name(self) -> str:
        if self.verifier_contract is None:
            return ''
        else:
            assert isinstance(self.verifier_contract.contract_type.type_name, UserDefinedTypeName)
            return self.verifier_contract.contract_type.type_name.names[0]

    @staticmethod
    def get_type(expr: Expression, privacy: PrivacyLabelExpr) -> TypeName:
        return expr.annotated_type.type_name if privacy.is_all_expr() else TypeName.cipher_type()

    def requires_verification(self) -> bool:
        """ Returns true if the function corresponding to this circuit requires a zk proof verification for correctness """
        return self.p or self.s

    def request_public_key(self, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        pname = privacy.idf.name
        if pname in self.pk_for_label:
            return self.pk_for_label[pname].lhs.arr.idf
        else:
            idf = self.in_name_factory.get_new_idf(TypeName.key_type())
            pki_idf = self.used_contracts[0].state_variable_idf
            assert pki_idf
            self.pk_for_label[pname] = AssignmentStatement(
                idf.get_loc_expr(), FunctionCallExpr(MemberAccessExpr(IdentifierExpr(pki_idf), Identifier('getPk')),
                                                     [self.expr_trafo.visit(privacy)])
            )
            return idf

    def add_param(self, expr: Expression, privacy: PrivacyLabelExpr) -> HybridArgumentIdf:
        t = self.get_type(expr, privacy)
        idf = self.out_name_factory.get_new_idf(t)
        return idf

    def add_temp_var(self, expr: Expression, privacy: PrivacyLabelExpr, enc_param: bool) -> HybridArgumentIdf:
        te = self.expr_trafo.visit(expr)
        te_t = self.get_type(expr, privacy)

        if te_t == TypeName.bool_type():
            te = te.implicitly_converted(TypeName.uint_type())

        idf = self.in_name_factory.get_new_idf(te_t)
        stmt = AssignmentStatement(idf.get_loc_expr(), te)
        if enc_param:
            self.enc_param_check_stmts.append(stmt)
        else:
            assert expr.statement is not None and expr.statement in self.old_code_and_temp_var_decls_for_stmt
            self.old_code_and_temp_var_decls_for_stmt[expr.statement][1].append(stmt)
        return idf

    def ensure_encryption(self, plain: HybridArgumentIdf, new_privacy: PrivacyLabelExpr, cipher: HybridArgumentIdf):
        rnd = HybridArgumentIdf(f'{cipher.get_flat_name()}_R', None, TypeName.rnd_type())

        if isinstance(plain, EncParamIdf):
            self.s.append(plain)
            cipher = self.add_temp_var(cipher.get_loc_expr(AnnotatedTypeName.cipher_type()), Expression.me_expr(), True)

        self.s.append(rnd)

        pk = self.request_public_key(new_privacy)
        self.p.append(pk)

        self.p.append(cipher)
        self.phi.append(EncConstraint(plain, rnd, pk, cipher))

    def move_out(self, expr: Expression, new_privacy: PrivacyLabelExpr):
        new_param = self.add_param(expr, new_privacy)

        from zkay.compiler.privacy.transformer.zkay_transformer import ZkayCircuitTransformer
        rhs_expr = ZkayCircuitTransformer(self).visit(expr)
        new_param.corresponding_expression = IdfValue(new_privacy, rhs_expr)
        sec_circ_var_idf = self.local_expr_name_factory.get_new_idf(expr.annotated_type.type_name)
        self.phi.append(ExpressionToLocAssignment(sec_circ_var_idf, rhs_expr))

        if not new_privacy.is_all_expr():
            self.ensure_encryption(sec_circ_var_idf, new_privacy, new_param)
            return expr.replaced_with(new_param.get_loc_expr(), AnnotatedTypeName.cipher_type())
        else:
            self.p.append(new_param)
            self.phi.append(EqConstraint(sec_circ_var_idf, new_param))
            return expr.replaced_with(new_param.get_loc_expr(), AnnotatedTypeName.uint_all()).implicitly_converted(new_param.t)

    def move_in(self, loc_expr: LocationExpr, privacy: PrivacyLabelExpr):
        new_var = self.add_temp_var(loc_expr, privacy, False)
        self.p.append(new_var)

        if privacy.is_me_expr():
            # Instead of secret key, decrypt outside proof circuit (but locally), add plain value as secret param
            #  and prove encryption (because its not feasible to decrypt inside proof circuit)
            dec_loc_idf = self.secret_input_name_factory.get_new_idf(loc_expr.annotated_type.type_name)
            self.s.append(dec_loc_idf)
            self.ensure_encryption(dec_loc_idf, Expression.me_expr(), deepcopy(new_var))
            new_var.corresponding_plaintext_circuit_input = dec_loc_idf

        return loc_expr.replaced_with(new_var.get_loc_expr(), AnnotatedTypeName.cipher_type())
