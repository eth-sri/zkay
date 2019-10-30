import os
import re
from subprocess import SubprocessError
from textwrap import dedent

from zkay.compiler.privacy.library_contracts import should_use_hash
from zkay.compiler.privacy.circuit_generation.circuit_generator import CircuitGenerator
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, CircuitStatement, ExpressionToLocAssignment, EqConstraint, \
    EncConstraint, HybridArgumentIdf
from zkay.compiler.privacy.proving_schemes.gm17 import ProvingSchemeGm17, VerifyingKeyGm17
from zkay.compiler.privacy.proving_schemes.proving_scheme import VerifyingKey, G2Point, G1Point
from zkay.utils.run_command import run_command
from zkay.utils.timer import time_measure
from zkay.zkay_ast.ast import CodeVisitor, FunctionCallExpr, BuiltinFunction, TypeName, NumberLiteralExpr, Expression, \
    AnnotatedTypeName, AssignmentStatement, IdentifierExpr, Identifier, BooleanLiteralExpr, IndexExpr, indent

expected_hash_name = 'zk_expected_hash'
zok_bin = 'zokrates'
if 'ZOKRATES_ROOT' in os.environ:
    # could also be a path
    zok_bin = os.path.join(os.environ['ZOKRATES_ROOT'], 'zokrates')


class ZokratesCodeVisitor(CodeVisitor):
    @staticmethod
    def as_bool(expr: Expression) -> Expression:
        if not isinstance(expr, BooleanLiteralExpr) and expr.annotated_type.type_name != TypeName.bool_type():
            expr = expr.replaced_with(FunctionCallExpr(BuiltinFunction('!='), [expr, NumberLiteralExpr(0)]))
        expr.annotated_type = AnnotatedTypeName.bool_all()
        return expr

    @staticmethod
    def as_int(expr: Expression) -> Expression:
        if not isinstance(expr, NumberLiteralExpr) and expr.annotated_type.type_name == TypeName.bool_type():
            expr = expr.replaced_with(FunctionCallExpr(BuiltinFunction('ite'), [expr, NumberLiteralExpr(1), NumberLiteralExpr(0)]))
        expr.annotated_type = AnnotatedTypeName.uint_all()
        return expr

    def visitIndexExpr(self, ast: IndexExpr):
        if isinstance(ast.arr, IdentifierExpr) and isinstance(ast.arr.idf, HybridArgumentIdf):
            corresponding_plain_input = ast.arr.idf.corresponding_plaintext_circuit_input
            if corresponding_plain_input is not None:
                return self.visit(corresponding_plain_input)
        return super().visitIndexExpr(ast)

    def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
        return '(1 == 1)' if ast.value else '(0 == 1)'

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        return f'{self.visit(ast.lhs)} = {self.visit(self.as_int(ast.rhs))}'

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            if ast.func.op == 'ite':
                cond = self.visit(self.as_bool(ast.args[0]))
                t = self.visit(ast.args[1])
                e = self.visit(ast.args[2])
                return f'if ({cond}) then ({t}) else ({e}) fi'
            elif ast.func.op == '!=':
                ast.func.op = '=='
                return f'! ({self.visitFunctionCallExpr(ast)})'
            elif ast.func.is_bop():
                ast.args = [self.as_bool(arg) for arg in ast.args]
            elif ast.func.op == '==' or ast.func.is_comp():
                ast.args = [self.as_int(arg) for arg in ast.args]
        else:
            ast.args = [self.as_int(arg) for arg in ast.args]

        return super().visitFunctionCallExpr(ast)


class ZokratesGenerator(CircuitGenerator):
    zkvisitor = ZokratesCodeVisitor()
    g1_point_pattern = r'(0x[0-9a-f]{64}), (0x[0-9a-f]{64})'
    g2_point_pattern = f'\\[{g1_point_pattern}\\], \\[{g1_point_pattern}\\]'

    def _generate_zkcircuit(self, circuit: CircuitHelper):
        n_in, n_out = circuit.in_base_name, circuit.out_base_name
        pub_in_count, pub_out_count = circuit.in_name_factory.count, circuit.out_name_factory.count
        should_hash = should_use_hash(pub_in_count + pub_out_count)

        sec_args = [s.name for s in circuit.s]
        pub_args = []
        if pub_in_count > 0:
            pub_args.append((n_in, pub_in_count))
        if pub_out_count > 0:
            pub_args.append((n_out, pub_out_count))

        if should_hash:
            actual_sec_args = [f'private field {arg}' for arg in sec_args] + [f'private field[{arg[1]}] {arg[0]}' for arg in pub_args]
            actual_pub_args = []
            imports = hash_imports
            return_code = get_hash_code(n_in, pub_in_count, n_out, pub_out_count)
        else:
            actual_sec_args = [f'private field {arg}' for arg in sec_args]
            actual_pub_args = [f'field[{arg[1]}] {arg[0]}' for arg in pub_args]
            imports = ''
            return_code = 'return 1'
        argstr = ', '.join(actual_sec_args + actual_pub_args)

        zok_code = imports + lib_code
        zok_code += f'def main({argstr}) -> (field):\n'
        zok_code += indent('// Zkay constraints\n')
        zok_code += indent('\n'.join(dedent(e) for e in [self.__to_zok_code(stmt) for stmt in circuit.phi]) + '\n\n')
        zok_code += indent(return_code)

        dirname = os.path.join(self.output_dir, f'{circuit.get_circuit_name()}_out')
        if not os.path.exists(dirname):
            os.mkdir(dirname)

        with open(os.path.join(dirname, f'{circuit.get_circuit_name()}.zok'), 'w') as f:
            f.write(zok_code)

    def _generate_keys(self, circuit: CircuitHelper):
        odir = os.path.join(self.output_dir, f'{circuit.get_circuit_name()}_out')
        code_file_name = f'{circuit.get_circuit_name()}.zok'
        with time_measure('compileZokrates'):
            try:
                run_command([zok_bin, 'compile', '-i', code_file_name], cwd=odir)
            except SubprocessError as e:
                print(e)
                raise ValueError(f'Error compiling {code_file_name}') from e
        with time_measure('generatingKeyPair'):
            run_command([zok_bin, 'setup', '--proving-scheme', self.proving_scheme.name], cwd=odir)

    def _get_vk_and_pk_paths(self, circuit: CircuitHelper):
        odir = os.path.join(self.output_dir, f'{circuit.get_circuit_name()}_out')
        return os.path.join(odir, 'verification.key'), os.path.join(odir, 'proving.key')

    def _parse_verification_key(self, circuit: CircuitHelper) -> VerifyingKey:
        if isinstance(self.proving_scheme, ProvingSchemeGm17):
            with open(self._get_vk_and_pk_paths(circuit)[0]) as f:
                key_file = f.read()

            query = []
            for match in re.finditer(r'vk\.query\[\d+\] = ' + self.g1_point_pattern, key_file):
                query.append(G1Point.from_seq(match.groups()))

            key: VerifyingKeyGm17 = VerifyingKeyGm17(
                G2Point.from_seq(re.search(f'vk\\.h = {self.g2_point_pattern}', key_file).groups()),
                G1Point.from_seq(re.search(f'vk\\.g_alpha = {self.g1_point_pattern}', key_file).groups()),
                G2Point.from_seq(re.search(f'vk\\.h_beta = {self.g2_point_pattern}', key_file).groups()),
                G1Point.from_seq(re.search(f'vk\\.g_gamma = {self.g1_point_pattern}', key_file).groups()),
                G2Point.from_seq(re.search(f'vk\\.h_gamma = {self.g2_point_pattern}', key_file).groups()),
                query
            )
        else:
            assert False
        return key

    def __to_zok_code(self, stmt: CircuitStatement):
        if isinstance(stmt, ExpressionToLocAssignment):
            lhs = stmt.lhs.get_loc_expr(AnnotatedTypeName.uint_all())
            return f'field {self.zkvisitor.visit(AssignmentStatement(lhs, stmt.expr))}'
        elif isinstance(stmt, EqConstraint):
            return self.zkvisitor.visit(FunctionCallExpr(BuiltinFunction('=='),
                                                         [e.get_loc_expr(AnnotatedTypeName.uint_all()) for e in [stmt.tgt, stmt.val]]))
        else:
            assert isinstance(stmt, EncConstraint)
            fcall = FunctionCallExpr(IdentifierExpr(Identifier('enc')),
                                     [e.get_loc_expr(AnnotatedTypeName.uint_all()) for e in [stmt.plain, stmt.rnd, stmt.pk]])
            fcall.annotated_type = AnnotatedTypeName.uint_all()
            cipher = self.zkvisitor.visit(stmt.cipher.get_loc_expr(AnnotatedTypeName.uint_all()))
            return f'(if {cipher} == 0 then 0 else {self.zkvisitor.visit(fcall)} fi) == {cipher}'


hash_imports = '''\
import "hashes/sha256/IVconstants" as IVconstants
import "hashes/sha256/shaRoundNoBoolCheck" as sha256
import "utils/pack/nonStrictUnpack256" as unpack
import "utils/pack/pack256" as pack

'''

lib_code = '''\
def enc(field msg, field R, field key) -> (field):
    // artificial constraints ensuring every variable is used
    field impossible = if R == 0 && R == 1 then 1 else 0 fi
    impossible == 0
    field cipher = msg + key
    if cipher == 0 then 1 else 0 fi == 0
    return cipher

'''


def get_hash_code(in_n: str, in_count: int, out_n: str, out_count: int):
    """ Generate code to perform standard conform sha256 merkle-damgard hashing of the full input sequence """
    bit_msg_len = (in_count + out_count) * 256
    msg_len_64_bits_big_endian = [int(bool(bit_msg_len & (1 << bit))) for bit in range(63, -1, -1)]

    if (in_count + out_count) % 2 == 0:
        # two padding blocks (size in second block)
        count_with_padding = in_count + out_count + 2
        padding_block_args = f"[1{', 0' * 255}], \n"
        padding_block_args += f"[0{', 0' * 191}, {', '.join(map(str, msg_len_64_bits_big_endian))}]"
    else:
        # padding block + another block with size
        count_with_padding = in_count + out_count + 1
        padding_block_args = f"[1{', 0' * 191}, {', '.join(map(str, msg_len_64_bits_big_endian))}]"
    assert count_with_padding % 2 == 0

    unpack_args = ', '.join(filter(bool, [
                            ', '.join([f'unpack({in_n}[{i}])' for i in range(in_count)]),
                            ', '.join([f'unpack({out_n}[{i}])' for i in range(out_count)])]))

    return f"// Prepare hash input blocks\n" \
           f"field[{count_with_padding}][256] zk_hash_input = [" \
           f"{unpack_args},\n" \
           f"{indent(padding_block_args)}\n" \
           f"]\n" + dedent(f'''
            // Compute input hash
            digest =  IVconstants()
            for field i in 0..{count_with_padding // 2} do
                digest = sha256(zk_hash_input[2*i], zk_hash_input[2*i+1], digest)
            endfor

            return pack(digest)
           ''')
