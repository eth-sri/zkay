import os
from typing import Dict, List, Optional

from zkay.compiler.privacy.circuit_generation.circuit_generator import CircuitGenerator
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, CircuitStatement, \
    ExpressionToLocAssignment, EqConstraint, EncConstraint, HybridArgumentIdf
from zkay.compiler.privacy.proving_schemes.gm17 import ProvingSchemeGm17, VerifyingKeyGm17
from zkay.compiler.privacy.proving_schemes.proving_scheme import VerifyingKey, G2Point, G1Point
from zkay.jsnark_interface.jsnark_interface import jWire, jCircuitGenerator, jEncGadget, jBigint, jCondAssignmentGadget, run_jsnark
from zkay.jsnark_interface.libsnark_interface import libsnark_generate_keys
from zkay.zkay_ast.ast import FunctionCallExpr, BuiltinFunction, IdentifierExpr, BooleanLiteralExpr, \
    IndexExpr, NumberLiteralExpr
from zkay.zkay_ast.visitor.visitor import AstVisitor


class JsnarkVisitor(AstVisitor):
    def __init__(self, circuit: CircuitHelper, log=False):
        super().__init__('node-or-children', log)
        self.circuit = circuit
        self.generator: Optional[jCircuitGenerator] = None
        self.local_vars: Dict[str, List[jWire]] = {}

    def visitCircuit(self, generator: jCircuitGenerator, parameters: Dict[str, List[jWire]]):
        self.generator = generator
        self.local_vars = parameters
        for constr in self.circuit.phi:
            self.visitCircuitStatement(constr)

    def visitCircuitStatement(self, stmt: CircuitStatement):
        if isinstance(stmt, ExpressionToLocAssignment):
            lhs = self.visit(stmt.expr)
            self.local_vars[stmt.lhs.name] = [lhs]
        elif isinstance(stmt, EqConstraint):
            lhs = self.local_vars[stmt.tgt.name][0 if stmt.tgt.offset is None else stmt.tgt.offset]
            rhs = self.local_vars[stmt.val.name][0 if stmt.val.offset is None else stmt.val.offset]
            self.generator.addEqualityAssertion(lhs, rhs)
        else:
            assert isinstance(stmt, EncConstraint)
            plain = self.local_vars[stmt.plain.name][0 if stmt.plain.offset is None else stmt.plain.offset]
            pk = self.local_vars[stmt.pk.name][0 if stmt.pk.offset is None else stmt.pk.offset]
            rnd = self.local_vars[stmt.rnd.name][0 if stmt.rnd.offset is None else stmt.rnd.offset]
            expected_cipher = self.local_vars[stmt.cipher.name][0 if stmt.cipher.offset is None else stmt.cipher.offset]

            computed_cipher = jEncGadget(plain, pk, rnd, f'enc({stmt.plain.name}, {stmt.pk.name}, {stmt.rnd.name})').getOutputWires()[0]
            computed_cipher_with_default = jCondAssignmentGadget(expected_cipher, computed_cipher, self.generator.getZeroWire(), 'check_enc').getOutputWires()[0]
            self.generator.addEqualityAssertion(expected_cipher, computed_cipher_with_default)

    def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
        if ast.value:
            return self.generator.getOneWire()
        else:
            return self.generator.getZeroWire()

    def visitNumberLiteralExpr(self, ast: NumberLiteralExpr):
        return self.generator.createConstantWire(jBigint(str(ast.value)))

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        return self.local_vars[ast.idf.name][0]

    def visitIndexExpr(self, ast: IndexExpr):
        if isinstance(ast.arr, IdentifierExpr) and isinstance(ast.arr.idf, HybridArgumentIdf):
            corresponding_plain_input = ast.arr.idf.corresponding_plaintext_circuit_input
            if corresponding_plain_input is not None:
                return self.visit(corresponding_plain_input.get_loc_expr())

        assert isinstance(ast.arr, IdentifierExpr) and isinstance(ast.key, NumberLiteralExpr)
        return self.local_vars[ast.arr.idf.name][ast.key.value]

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            op = ast.func.op
            args = list(map(self.visit, ast.args))

            if op == 'ite':
                return jCondAssignmentGadget(args[0], args[1], args[2], 'ite').getOutputWires()[0]
            elif op == 'parenthesis':
                return args[0]

            elif op == 'sign+':
                return args[0]
            elif op == 'sign-':
                return args[0].mul(-1)

            elif op == '*':
                return args[0].mul(args[1])
            elif op == '+':
                return args[0].add(args[1])
            elif op == '-':
                return args[0].sub(args[1])

            elif op == '==':
                return args[0].isEqualTo(args[1])
            elif op == '!=':
                return args[0].sub(args[1]).checkNonZero()

            elif op == '<':
                return args[0].isLessThan(args[1], 253)
            elif op == '<=':
                return args[0].isLessThanOrEqual(args[1], 253)
            elif op == '>':
                return args[0].isGreaterThan(args[1], 253)
            elif op == '>=':
                return args[0].isGreaterThanOrEqual(args[1], 253)

            elif op == '&&':
                and_fct = getattr(args[0], 'and')
                return and_fct(args[1])
            elif op == '||':
                or_fct = getattr(args[0], 'or')
                return or_fct(args[1])
            elif op == '!':
                return args[0].invAsBits()

        raise ValueError(f'Unsupported function {ast.func.code()} inside circuit')


class JsnarkGenerator(CircuitGenerator):
    def _generate_zkcircuit(self, circuit: CircuitHelper):
        output_dir = self._get_circuit_output_dir(circuit)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        visitor = JsnarkVisitor(circuit)
        run_jsnark(visitor, circuit, output_dir)

    def _generate_keys(self, circuit: CircuitHelper):
        output_dir = self._get_circuit_output_dir(circuit)
        libsnark_generate_keys(output_dir, self.proving_scheme.name)

    def _get_vk_and_pk_paths(self, circuit: CircuitHelper):
        output_dir = self._get_circuit_output_dir(circuit)
        return os.path.join(output_dir, 'verification.key'), os.path.join(output_dir, 'proving.key')

    def _parse_verification_key(self, circuit: CircuitHelper) -> VerifyingKey:
        with open(self._get_vk_and_pk_paths(circuit)[0]) as f:
            data = iter(f.read().splitlines())
        if isinstance(self.proving_scheme, ProvingSchemeGm17):
            h = G2Point(next(data), next(data), next(data), next(data))
            g_alpha = G1Point(next(data), next(data))
            h_beta = G2Point(next(data), next(data), next(data), next(data))
            g_gamma = G1Point(next(data), next(data))
            h_gamma = G2Point(next(data), next(data), next(data), next(data))
            query_len = int(next(data))
            query: List[Optional[G1Point]] = [None for _ in range(query_len)]
            for idx in range(query_len):
                query[idx] = G1Point(next(data), next(data))
            return VerifyingKeyGm17(h, g_alpha, h_beta, g_gamma, h_gamma, query)
        else:
            raise NotImplementedError()

    def _get_primary_inputs(self, should_hash: bool, circuit: CircuitHelper) -> List[str]:
        return ['1'] + super()._get_primary_inputs(should_hash, circuit)
