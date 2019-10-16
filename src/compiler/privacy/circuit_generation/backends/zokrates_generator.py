import os
import re
from textwrap import dedent

from compiler.privacy.circuit_generation.circuit_generator import CircuitGenerator
from compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, CircuitStatement, ExpressionToLocAssignment, EqConstraint, \
    EncConstraint
from compiler.privacy.proving_schemes.gm17 import ProvingSchemeGm17, VerifyingKeyGm17
from compiler.privacy.proving_schemes.proving_scheme import VerifyingKey, G2Point, G1Point

g1_point_pattern = r'(0x[0-9a-f]{64}), (0x[0-9a-f]{64})'
g2_point_pattern = f'\\[{g1_point_pattern}\\], \\[{g1_point_pattern}\\]'


class ZokratesGenerator(CircuitGenerator):
    def to_zok_code(self, stmt: CircuitStatement):
        if isinstance(stmt, ExpressionToLocAssignment):
            return f'field {stmt.lhs.name} = {stmt.expr.code()}'
        elif isinstance(stmt, EqConstraint):
            return f'{stmt.expr.name} == {stmt.val.name}'
        else:
            assert isinstance(stmt, EncConstraint)
            return f'enc({stmt.plain.name}, {stmt.rnd.name}, {stmt.pk.name}) == {stmt.cipher.name}'

    def _generate_zkcircuit(self, circuit: CircuitHelper):
        secret_args = ', '.join([f'private field {s.name}' for s in circuit.s])

        pub_out_count = circuit.param_name_factory.count
        pub_in_count = circuit.temp_name_factory.count

        public_args = f'field[{pub_in_count}] {circuit.temp_base_name}, field[{pub_out_count}] {circuit.param_base_name}'
        zok_code = lib_code + dedent(f'''\
            def main({", ".join([secret_args, public_args])}):\
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
        pass

    def _parse_verification_key(self, circuit: CircuitHelper) -> VerifyingKey:
        if isinstance(self.proving_scheme, ProvingSchemeGm17):
            return self.proving_scheme.dummy_vk()
            with open(os.path.join(self.output_dir, f'{circuit.get_circuit_name()}_out', 'verification.key')) as f:
                key_file = f.read()

            query = []
            for match in re.finditer(r'vk.query\[\d+\] = ' + g2_point_pattern, key_file):
                query.append(G1Point.from_seq(match.groups()))

            key: VerifyingKeyGm17 = VerifyingKeyGm17(
                G2Point.from_seq(re.search(f'vk.H = {g2_point_pattern}', key_file).groups()),
                G1Point.from_seq(re.search(f'vk.Galpha = {g1_point_pattern}', key_file).groups()),
                G1Point.from_seq(re.search(f'vk.Hbeta = {g1_point_pattern}', key_file).groups()),
                G1Point.from_seq(re.search(f'vk.Ggamma = {g1_point_pattern}', key_file).groups()),
                G2Point.from_seq(re.search(f'vk.Hgamma = {g2_point_pattern}', key_file).groups()),
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