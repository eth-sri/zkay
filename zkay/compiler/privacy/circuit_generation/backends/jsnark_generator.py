"""Circuit Generator implementation for the jsnark backend"""

import os
from typing import List, Optional, Union, Tuple

import zkay.jsnark_interface.jsnark_interface as jsnark
import zkay.jsnark_interface.libsnark_interface as libsnark
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircComment, CircIndentBlock, \
    CircGuardModification, CircCall, CircSymmEncConstraint
from zkay.compiler.privacy.circuit_generation.circuit_generator import CircuitGenerator
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, CircuitStatement, \
    CircVarDecl, CircEqConstraint, CircEncConstraint, HybridArgumentIdf
from zkay.compiler.privacy.proving_scheme.backends.gm17 import ProvingSchemeGm17
from zkay.compiler.privacy.proving_scheme.backends.groth16 import ProvingSchemeGroth16
from zkay.compiler.privacy.proving_scheme.proving_scheme import VerifyingKey, G2Point, G1Point, ProvingScheme
from zkay.config import cfg, zk_print
from zkay.utils.helpers import hash_file, hash_string
from zkay.zkay_ast.ast import FunctionCallExpr, BuiltinFunction, IdentifierExpr, BooleanLiteralExpr, \
    IndexExpr, MeExpr, NumberLiteralExpr, MemberAccessExpr, TypeName, indent, PrimitiveCastExpr, EnumDefinition, \
    Expression
from zkay.zkay_ast.homomorphism import Homomorphism
from zkay.zkay_ast.visitor.visitor import AstVisitor


def _get_t(t: Union[TypeName, Expression]):
    """Return the corresponding jsnark type name for a given type or expression."""
    if isinstance(t, Expression):
        t = t.annotated_type.type_name
    bits = t.elem_bitwidth
    if t.elem_bitwidth == 1:
        return 'ZkBool'
    if t.is_signed_numeric:
        return f'ZkInt({bits})'
    else:
        return f'ZkUint({bits})'


class JsnarkVisitor(AstVisitor):
    """Visitor which compiles CircuitStatements and Expressions down to java code compatible with a custom jsnark wrapper."""

    def __init__(self, phi: List[CircuitStatement]):
        super().__init__('node-or-children', False)
        self.phi = phi

    def visitCircuit(self) -> List[str]:
        return [self.visit(constr) for constr in self.phi]

    def visitCircComment(self, stmt: CircComment):
        return f'// {stmt.text}' if stmt.text else ''

    def visitCircIndentBlock(self, stmt: CircIndentBlock):
        stmts = list(map(self.visit, stmt.statements))
        if stmt.name:
            return f'//[ --- {stmt.name} ---\n' + indent('\n'.join(stmts)) + '\n' + f'//] --- {stmt.name} ---\n'
        else:
            return indent('\n'.join(stmts))

    def visitCircCall(self, stmt: CircCall):
        return f'_{stmt.fct.name}();'

    def visitCircVarDecl(self, stmt: CircVarDecl):
        return f'decl("{stmt.lhs.name}", {self.visit(stmt.expr)});'

    def visitCircEqConstraint(self, stmt: CircEqConstraint):
        assert stmt.tgt.t.size_in_uints == stmt.val.t.size_in_uints
        return f'checkEq("{stmt.tgt.name}", "{stmt.val.name}");'

    def visitCircEncConstraint(self, stmt: CircEncConstraint):
        assert stmt.cipher.t.is_cipher()
        assert stmt.pk.t.is_key()
        assert stmt.rnd.t.is_randomness()
        assert stmt.cipher.t.crypto_params == stmt.pk.t.crypto_params == stmt.rnd.t.crypto_params
        backend = stmt.pk.t.crypto_params.crypto_name
        if stmt.is_dec:
            return f'checkDec("{backend}", "{stmt.plain.name}", "{stmt.pk.name}", "{stmt.rnd.name}", "{stmt.cipher.name}");'
        else:
            return f'checkEnc("{backend}", "{stmt.plain.name}", "{stmt.pk.name}", "{stmt.rnd.name}", "{stmt.cipher.name}");'

    def visitCircSymmEncConstraint(self, stmt: CircSymmEncConstraint):
        assert stmt.iv_cipher.t.is_cipher()
        assert stmt.other_pk.t.is_key()
        assert stmt.iv_cipher.t.crypto_params == stmt.other_pk.t.crypto_params
        backend = stmt.other_pk.t.crypto_params.crypto_name
        if stmt.is_dec:
            return f'checkSymmDec("{backend}", "{stmt.plain.name}", "{stmt.other_pk.name}", "{stmt.iv_cipher.name}");'
        else:
            return f'checkSymmEnc("{backend}", "{stmt.plain.name}", "{stmt.other_pk.name}", "{stmt.iv_cipher.name}");'

    def visitCircGuardModification(self, stmt: CircGuardModification):
        if stmt.new_cond is None:
            return 'popGuard();'
        else:
            return f'addGuard("{stmt.new_cond.name}", {str(stmt.is_true).lower()});'

    def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
        return f'val({str(ast.value).lower()})'

    def visitNumberLiteralExpr(self, ast: NumberLiteralExpr):
        t = _get_t(ast)
        if ast.value < (1 << 31):
            return f'val({ast.value}, {t})'
        else:
            return f'val("{ast.value}", {t})'

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if isinstance(ast.idf, HybridArgumentIdf) and ast.idf.t.is_cipher():
            return f'getCipher("{ast.idf.name}")'
        else:
            return f'get("{ast.idf.name}")'

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        assert isinstance(ast.member, HybridArgumentIdf)
        if ast.member.t.is_cipher():
            return f'getCipher("{ast.member.name}")'
        else:
            assert ast.member.t.size_in_uints == 1
            return f'get("{ast.member.name}")'

    def visitIndexExpr(self, ast: IndexExpr):
        raise NotImplementedError()

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            assert ast.func.can_be_private()
            args = list(map(self.visit, ast.args))
            if ast.func.is_shiftop():
                assert ast.args[1].annotated_type.type_name.is_literal
                args[1] = ast.args[1].annotated_type.type_name.value

            op = ast.func.op
            op = '-' if op == 'sign-' else op

            homomorphism = ast.func.homomorphism
            if homomorphism == Homomorphism.NON_HOMOMORPHIC:
                f_start = 'o_('
            else:
                crypto_backend = cfg.get_crypto_params(homomorphism).crypto_name
                public_key_name = ast.public_key.name
                f_start = f'o_hom("{crypto_backend}", "{public_key_name}", '
                args = [f'HomomorphicInput.of({arg})' for arg in args]

            if op == 'ite':
                fstr = f"{f_start}{{}}, '?', {{}}, ':', {{}})"
            elif op == 'parenthesis':
                fstr = '({})'
            elif op == 'sign+':
                raise NotImplementedError()
            else:
                o = f"'{op}'" if len(op) == 1 else f'"{op}"'
                if len(args) == 1:
                    fstr = f"{f_start}{o}, {{}})"
                else:
                    assert len(args) == 2
                    fstr = f'{f_start}{{}}, {o}, {{}})'

            return fstr.format(*args)
        elif ast.is_cast and isinstance(ast.func.target, EnumDefinition):
            assert ast.annotated_type.type_name.elem_bitwidth == 256
            return self.handle_cast(self.visit(ast.args[0]), TypeName.uint_type())

        raise ValueError(f'Unsupported function {ast.func.code()} inside circuit')

    def visitPrimitiveCastExpr(self, ast: PrimitiveCastExpr):
        return self.handle_cast(self.visit(ast.expr), ast.elem_type)

    def handle_cast(self, wire, t: TypeName):
        return f'cast({wire}, {_get_t(t)})'


def add_function_circuit_arguments(circuit: CircuitHelper):
    """Generate java code which adds circuit IO as described by circuit"""

    input_init_stmts = []
    for sec_input in circuit.sec_idfs:
        input_init_stmts.append(f'addS("{sec_input.name}", {sec_input.t.size_in_uints}, {_get_t(sec_input.t)});')

    for pub_input in circuit.input_idfs:
        if pub_input.t.is_key():
            backend = pub_input.t.crypto_params.crypto_name
            input_init_stmts.append(f'addK("{backend}", "{pub_input.name}", {pub_input.t.size_in_uints});')
        else:
            input_init_stmts.append(f'addIn("{pub_input.name}", {pub_input.t.size_in_uints}, {_get_t(pub_input.t)});')

    for pub_output in circuit.output_idfs:
        input_init_stmts.append(f'addOut("{pub_output.name}", {pub_output.t.size_in_uints}, {_get_t(pub_output.t)});')

    sec_input_names = [sec_input.name for sec_input in circuit.sec_idfs]
    for crypto_params in cfg.all_crypto_params():
        pk_name = circuit.get_glob_key_name(MeExpr(), crypto_params)
        sk_name = circuit.get_own_secret_key_name(crypto_params)
        if crypto_params.is_symmetric_cipher() and sk_name in sec_input_names:
            assert pk_name in [pub_input.name for pub_input in circuit.input_idfs]
            input_init_stmts.append(f'setKeyPair("{crypto_params.crypto_name}", "{pk_name}", "{sk_name}");')

    return input_init_stmts


class JsnarkGenerator(CircuitGenerator):
    def __init__(self, circuits: List[CircuitHelper], proving_scheme: ProvingScheme, output_dir: str):
        super().__init__(circuits, proving_scheme, output_dir, False)

    def _generate_zkcircuit(self, import_keys: bool, circuit: CircuitHelper) -> bool:
        # Create output directory
        output_dir = self._get_circuit_output_dir(circuit)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        # Generate java code to add used crypto backends by calling addCryptoBackend
        crypto_init_stmts = []
        for params in circuit.fct.used_crypto_backends:
            init_stmt = f'addCryptoBackend("{params.crypto_name}", "{params.crypto_name}", {params.key_bits});'
            crypto_init_stmts.append(init_stmt)

        # Generate java code for all functions which are transitively called by the fct corresponding to this circuit
        # (outside private expressions)
        fdefs = []
        for fct in list(circuit.transitively_called_functions.keys()):
            target_circuit = self.circuits[fct]
            body_stmts = JsnarkVisitor(target_circuit.phi).visitCircuit()

            body = '\n'.join([f'stepIn("{fct.name}");'] +
                             add_function_circuit_arguments(target_circuit) + [''] +
                             [stmt for stmt in body_stmts] +
                             ['stepOut();'])
            fdef = f'private void _{fct.name}() {{\n' + indent(body) + '\n}'
            fdefs.append(f'{fdef}')

        # Generate java code for the function corresponding to this circuit
        input_init_stmts = add_function_circuit_arguments(circuit)
        constraints = JsnarkVisitor(circuit.phi).visitCircuit()

        # Inject the function definitions into the java template
        code = jsnark.get_jsnark_circuit_class_str(circuit, crypto_init_stmts, fdefs, input_init_stmts + [''] + constraints)

        # Compute combined hash of the current jsnark interface jar and of the contents of the java file
        hashfile = os.path.join(output_dir, f'{cfg.jsnark_circuit_classname}.hash')
        digest = hash_string((jsnark.circuit_builder_jar_hash + code + cfg.proving_scheme).encode('utf-8')).hex()
        if os.path.exists(hashfile):
            with open(hashfile, 'r') as f:
                oldhash = f.read()
        else:
            oldhash = ''

        # Invoke jsnark compilation if either the jsnark-wrapper or the current circuit was modified (based on hash comparison)
        if oldhash != digest or not os.path.exists(os.path.join(output_dir, 'circuit.arith')):
            if not import_keys:
                # Remove old keys
                for f in self._get_vk_and_pk_paths(circuit):
                    if os.path.exists(f):
                        os.remove(f)
            jsnark.compile_circuit(output_dir, code)
            with open(hashfile, 'w') as f:
                f.write(digest)
            return True
        else:
            zk_print(f'Circuit \'{circuit.get_verification_contract_name()}\' not modified, skipping compilation')
            return False

    def _generate_keys(self, circuit: CircuitHelper):
        # Invoke the custom libsnark interface to generate keys
        output_dir = self._get_circuit_output_dir(circuit)
        libsnark.generate_keys(output_dir, output_dir, self.proving_scheme.name)

    @classmethod
    def get_vk_and_pk_filenames(cls) -> Tuple[str, ...]:
        return 'verification.key', 'proving.key', 'verification.key.bin'

    def _parse_verification_key(self, circuit: CircuitHelper) -> VerifyingKey:
        with open(self._get_vk_and_pk_paths(circuit)[0]) as f:
            data = iter(f.read().splitlines())
        if isinstance(self.proving_scheme, ProvingSchemeGroth16):
            a = G1Point.from_it(data)
            b = G2Point.from_it(data)
            gamma = G2Point.from_it(data)
            delta = G2Point.from_it(data)
            query_len = int(next(data))
            gamma_abc: List[Optional[G1Point]] = [None for _ in range(query_len)]
            for idx in range(query_len):
                gamma_abc[idx] = G1Point.from_it(data)
            return ProvingSchemeGroth16.VerifyingKey(a, b, gamma, delta, gamma_abc)
        elif isinstance(self.proving_scheme, ProvingSchemeGm17):
            h = G2Point.from_it(data)
            g_alpha = G1Point.from_it(data)
            h_beta = G2Point.from_it(data)
            g_gamma = G1Point.from_it(data)
            h_gamma = G2Point.from_it(data)
            query_len = int(next(data))
            query: List[Optional[G1Point]] = [None for _ in range(query_len)]
            for idx in range(query_len):
                query[idx] = G1Point.from_it(data)
            return ProvingSchemeGm17.VerifyingKey(h, g_alpha, h_beta, g_gamma, h_gamma, query)
        else:
            raise NotImplementedError()

    def _get_prover_key_hash(self, circuit: CircuitHelper) -> bytes:
        return hash_file(self._get_vk_and_pk_paths(circuit)[1])

    def _get_primary_inputs(self, circuit: CircuitHelper) -> List[str]:
        # Jsnark requires an additional public input with the value 1 as first input
        return ['1'] + super()._get_primary_inputs(circuit)
