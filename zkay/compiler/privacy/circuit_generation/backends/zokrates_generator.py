import os
import re
from subprocess import SubprocessError
from typing import Tuple, List

from zkay.compiler.privacy.circuit_generation.circuit_generator import CircuitGenerator
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, CircuitStatement, \
    CircVarDecl, CircEqConstraint, CircEncConstraint, HybridArgumentIdf
from zkay.config import cfg
from zkay.compiler.privacy.proving_schemes.gm17 import ProvingSchemeGm17, VerifyingKeyGm17
from zkay.compiler.privacy.proving_schemes.proving_scheme import VerifyingKey, G2Point, G1Point, ProvingScheme
from zkay.utils.multiline_formatter import MultiLineFormatter
from zkay.utils.run_command import run_command
from zkay.utils.timer import time_measure
from zkay.zkay_ast.ast import CodeVisitor, FunctionCallExpr, BuiltinFunction, TypeName, AnnotatedTypeName, \
    AssignmentStatement, IdentifierExpr, Identifier, BooleanLiteralExpr, IndexExpr, AST

zok_bin = 'zokrates'
if 'ZOKRATES_ROOT' in os.environ:
    # could also be a path
    zok_bin = os.path.join(os.environ['ZOKRATES_ROOT'], 'zokrates')


class ZokratesCodeVisitor(CodeVisitor):
    def visitIndexExpr(self, ast: IndexExpr):
        if isinstance(ast.arr, IdentifierExpr) and isinstance(ast.arr.idf, HybridArgumentIdf):
            corresponding_plain_input = ast.arr.idf.corresponding_plaintext_circuit_input
            if corresponding_plain_input is not None:
                return self.visit(corresponding_plain_input)
        return super().visitIndexExpr(ast)

    def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
        return '(1 == 1)' if ast.value else '(0 == 1)'

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        return f'{self.visit(ast.lhs)} = {self.visit(ast.rhs.implicitly_converted(TypeName.uint_type()))}'

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            if ast.func.op == 'ite':
                cond = self.visit(ast.args[0].implicitly_converted(TypeName.bool_type()))
                t = self.visit(ast.args[1])
                e = self.visit(ast.args[2])
                return f'if ({cond}) then ({t}) else ({e}) fi'
            elif ast.func.op == '!=':
                ast.func.op = '=='
                return f'! ({self.visitFunctionCallExpr(ast)})'
            elif ast.func.is_bop():
                ast.args = [arg.implicitly_converted(TypeName.bool_type()) for arg in ast.args]
            elif ast.func.op == '==' or ast.func.is_comp():
                ast.args = [arg.implicitly_converted(TypeName.uint_type()) for arg in ast.args]
        else:
            ast.args = [arg.implicitly_converted(TypeName.uint_type())for arg in ast.args]

        return super().visitFunctionCallExpr(ast)

    def visitCircuitStatement(self, stmt: CircuitStatement):
        if isinstance(stmt, CircVarDecl):
            lhs = stmt.lhs.get_loc_expr(AnnotatedTypeName.uint_all())
            return f'field {self.visit(AssignmentStatement(lhs, stmt.expr))}'
        elif isinstance(stmt, CircEqConstraint):
            return self.visit(FunctionCallExpr(BuiltinFunction('=='),
                                                         [e.get_loc_expr(AnnotatedTypeName.uint_all()) for e in [stmt.tgt, stmt.val]]))
        else:
            assert isinstance(stmt, CircEncConstraint)
            fcall = FunctionCallExpr(IdentifierExpr(Identifier('enc')),
                                     [e.get_loc_expr(AnnotatedTypeName.uint_all()) for e in [stmt.plain, stmt.rnd, stmt.pk]])
            fcall.annotated_type = AnnotatedTypeName.uint_all()
            cipher = self.visit(stmt.cipher.get_loc_expr(AnnotatedTypeName.uint_all()))
            return f'(if {cipher} == 0 then 0 else {self.visit(fcall)} fi) == {cipher}'


class ZokratesGenerator(CircuitGenerator):
    zkvisitor = ZokratesCodeVisitor()
    g1_point_pattern = r'(0x[0-9a-f]{64}), (0x[0-9a-f]{64})'
    g2_point_pattern = f'\\[{g1_point_pattern}\\], \\[{g1_point_pattern}\\]'

    hash_imports = '''\
    import "hashes/sha256/IVconstants" as IVconstants
    import "hashes/sha256/shaRoundNoBoolCheck" as sha256
    import "utils/pack/nonStrictUnpack256" as unpack
    import "utils/pack/pack256" as pack
    '''

    def __init__(self, transformed_ast: AST, circuits: List[CircuitHelper], proving_scheme: ProvingScheme, output_dir: str):
        super().__init__(transformed_ast, circuits, proving_scheme, output_dir, True)

    def _generate_zkcircuit(self, circuit: CircuitHelper) -> bool:
        sec_args = [s.name for s in circuit.sec_idfs]
        pub_args = circuit.public_arg_arrays
        tot_count = sum(map(lambda x: x[1], pub_args))

        if cfg.should_use_hash(tot_count):
            actual_sec_args = [f'private field {arg}' for arg in sec_args] + [f'private field[{arg[1]}] {arg[0]}' for arg in pub_args]
            actual_pub_args = []
            imports = self.hash_imports
            after_body_code = self.__get_hash_code(pub_args, tot_count)
        else:
            actual_sec_args = [f'private field {arg}' for arg in sec_args]
            actual_pub_args = [f'field[{arg[1]}] {arg[0]}' for arg in pub_args]
            imports = ''
            after_body_code = 'return 1'
        argstr = ', '.join(actual_sec_args + actual_pub_args)

        zok_code = MultiLineFormatter() * \
        imports * '\
        def enc(field msg, field R, field key) -> (field):' / f'''\
            // artificial constraints ensuring every variable is used
            field impossible = if R == 0 && R == 1 then 1 else 0 fi
            impossible == 0
            field cipher = msg + key
            if cipher == 0 then 1 else 0 fi == 0
            return cipher
        ''' // f'\
        def main({argstr}) -> (field):' / \
            '// Zkay constraints' * \
            [self.zkvisitor.visitCircuitStatement(stmt) for stmt in circuit.phi] * '' * \
            after_body_code

        output_dir = self._get_circuit_output_dir(circuit)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        code_file_name = f'{circuit.get_circuit_name()}.zok'
        with open(os.path.join(output_dir, code_file_name), 'w') as f:
            f.write(str(zok_code))

        with time_measure('compileZokrates'):
            try:
                run_command([zok_bin, 'compile', '-i', code_file_name], cwd=output_dir)
            except SubprocessError as e:
                print(e)
                raise ValueError(f'Error compiling {code_file_name}') from e

        return True

    @staticmethod
    def __get_hash_code(pub_args: List[Tuple[str, int]], total_count: int) -> str:
        """ Generate code to perform standard conform sha256 merkle-damgard hashing of the full input sequence """
        bit_msg_len = total_count * 256
        msg_len_64_bits_big_endian = [int(bool(bit_msg_len & (1 << bit))) for bit in range(63, -1, -1)]

        if total_count % 2 == 0:
            # two padding blocks (size in second block)
            count_with_padding = total_count + 2
            padding_block_args = f"[1{', 0' * 255}], \n"
            padding_block_args += f"[0{', 0' * 191}, {', '.join(map(str, msg_len_64_bits_big_endian))}]"
        else:
            # padding block + another block with size
            count_with_padding = total_count + 1
            padding_block_args = f"[1{', 0' * 191}, {', '.join(map(str, msg_len_64_bits_big_endian))}]"

        unpack_args = ', '.join([', '.join([f'unpack({name}[{i}])' for i in range(count)]) for name, count in pub_args])

        code = MultiLineFormatter() * f'''\
        // Prepare hash input blocks
        field[{count_with_padding}][256] zk_hash_input = [''' / \
            unpack_args % '' * \
            padding_block_args // f'''\
        ]

        // Compute input hash
        digest =  IVconstants()
        for field i in 0..{count_with_padding // 2} do
            digest = sha256(zk_hash_input[2*i], zk_hash_input[2*i+1], digest)
        endfor

        return pack(digest)'''
        return str(code)

    def _generate_keys(self, circuit: CircuitHelper):
        output_dir = self._get_circuit_output_dir(circuit)
        with time_measure('generatingKeyPair'):
            run_command([zok_bin, 'setup', '--proving-scheme', self.proving_scheme.name], cwd=output_dir)

    def _get_vk_and_pk_paths(self, circuit: CircuitHelper):
        output_dir = self._get_circuit_output_dir(circuit)
        return os.path.join(output_dir, 'verification.key'), os.path.join(output_dir, 'proving.key')

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
            raise NotImplementedError('Other proving schemes are currently not supported')
        return key

    def _get_primary_inputs(self, should_hash: bool, circuit: CircuitHelper) -> List[str]:
        inputs = super()._get_primary_inputs(should_hash, circuit)
        if not should_hash:
            inputs.append(1)
        return inputs
