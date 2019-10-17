import os
import re
from subprocess import SubprocessError
from textwrap import dedent

from compiler.privacy.circuit_generation.circuit_generator import CircuitGenerator
from compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, CircuitStatement, ExpressionToLocAssignment, EqConstraint, \
    EncConstraint
from compiler.privacy.proving_schemes.gm17 import ProvingSchemeGm17, VerifyingKeyGm17
from compiler.privacy.proving_schemes.proving_scheme import VerifyingKey, G2Point, G1Point
from utils.run_command import run_command
from utils.timer import time_measure
from zkay_ast.ast import CodeVisitor, FunctionCallExpr, BuiltinFunction, TypeName, NumberLiteralExpr

g1_point_pattern = r'(0x[0-9a-f]{64}), (0x[0-9a-f]{64})'
g2_point_pattern = f'\\[{g1_point_pattern}\\], \\[{g1_point_pattern}\\]'

zok_bin = 'zokrates'
if 'ZOKRATES_ROOT' in os.environ:
    # could also be a path
    zok_bin = os.path.join(os.environ['ZOKRATES_ROOT'], 'zokrates')


class ZokratesCodeVisitor(CodeVisitor):
    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction) and ast.func.is_ite():
            return f'if ({self.visit(ast.args[0])}) then ({self.visit(ast.args[1])}) else ({self.visit(ast.args[2])}) fi'
        else:
            return super().visitFunctionCallExpr(ast)


def compile_zokrates(output_dir: str, code_file_name: str, proving_scheme: str):
    with time_measure('compileZokrates'):
        # compile
        try:
            run_command([zok_bin, 'compile', '-i', code_file_name], cwd=output_dir)
        except SubprocessError as e:
            print(e)
            raise ValueError(f'Error compiling {code_file_name}') from e

        # setup
        run_command([zok_bin, 'setup', '--proving-scheme', proving_scheme], cwd=output_dir)


class ZokratesGenerator(CircuitGenerator):
    def to_zok_code(self, stmt: CircuitStatement):
        if isinstance(stmt, ExpressionToLocAssignment):
            expr = stmt.expr
            if stmt.lhs.t == TypeName.bool_type():
                expr = stmt.expr.replaced_with(FunctionCallExpr(BuiltinFunction('ite'), [expr, NumberLiteralExpr(1), NumberLiteralExpr(0)]))
            return f'field {stmt.lhs.name} = {ZokratesCodeVisitor().visit(expr)}'
        elif isinstance(stmt, EqConstraint):
            return f'{stmt.expr.name} == {stmt.val.name}'
        else:
            assert isinstance(stmt, EncConstraint)
            return f'enc({stmt.plain.name}, {stmt.rnd.name}, {stmt.pk.name}) == {stmt.cipher.name}'

    def _generate_zkcircuit(self, circuit: CircuitHelper):
        secret_args = ', '.join([f'private field {s.name}' for s in circuit.s])

        pub_in_count = circuit.temp_name_factory.count
        pub_out_count = circuit.param_name_factory.count
        pub_args = ', '.join(([f'field[{pub_in_count}] {circuit.temp_base_name}'] if pub_in_count > 0 else []) +
                             ([f'field[{pub_out_count}] {circuit.param_base_name}'] if pub_out_count > 0 else []))

        zok_code = lib_code + dedent(f'''\
            def main({", ".join([secret_args, pub_args])}) -> (field):\
                ''' + ''.join([f'''
                {self.to_zok_code(stmt)}''' for stmt in circuit.phi]) + f'''
                return 1
            ''')

        dirname = os.path.join(self.output_dir, f'{circuit.get_circuit_name()}_out')
        if not os.path.exists(dirname):
            os.mkdir(dirname)

        with open(os.path.join(dirname, f'{circuit.get_circuit_name()}.zok'), 'w') as f:
            f.write(zok_code)

    def _generate_keys(self, circuit: CircuitHelper):
        odir = os.path.join(self.output_dir, f'{circuit.get_circuit_name()}_out')
        compile_zokrates(odir, f'{circuit.get_circuit_name()}.zok', self.proving_scheme.name)

    def _get_vk_and_pk_paths(self, circuit: CircuitHelper):
        odir = os.path.join(self.output_dir, f'{circuit.get_circuit_name()}_out')
        return os.path.join(odir, 'verification.key'), os.path.join(odir, 'proving.key')

    def _parse_verification_key(self, circuit: CircuitHelper) -> VerifyingKey:
        if isinstance(self.proving_scheme, ProvingSchemeGm17):
            with open(self._get_vk_and_pk_paths(circuit)[0]) as f:
                key_file = f.read()

            query = []
            for match in re.finditer(r'vk\.query\[\d+\] = ' + g1_point_pattern, key_file):
                query.append(G1Point.from_seq(match.groups()))

            key: VerifyingKeyGm17 = VerifyingKeyGm17(
                G2Point.from_seq(re.search(f'vk\\.h = {g2_point_pattern}', key_file).groups()),
                G1Point.from_seq(re.search(f'vk\\.g_alpha = {g1_point_pattern}', key_file).groups()),
                G2Point.from_seq(re.search(f'vk\\.h_beta = {g2_point_pattern}', key_file).groups()),
                G1Point.from_seq(re.search(f'vk\\.g_gamma = {g1_point_pattern}', key_file).groups()),
                G2Point.from_seq(re.search(f'vk\\.h_gamma = {g2_point_pattern}', key_file).groups()),
                query
            )
        else:
            assert False
        return key


lib_code = '''\
def enc(field msg, field R, field key) -> (field):
    // artificial constraints ensuring every variable is used
    field impossible = if R == 0 && R == 1 then 1 else 0 fi
    impossible == 0
    return msg + key

'''