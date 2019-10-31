from typing import List

from zkay.compiler.zokrates.compiler import generate_proof
from zkay.transaction.interface import ZkayProverInterface, bn128_scalar_field


class ZokratesProver(ZkayProverInterface):
    def _generate_proof(self, verifier_dir: str, priv_values: List[int], in_vals: List[int], out_vals: List[int]) -> List[int]:
        args = list(map(int, priv_values + in_vals + out_vals))
        for arg in args:
            assert arg < bn128_scalar_field, "argument overflow"
        proof_data = generate_proof(f'{verifier_dir}_out', args, scheme=self.proving_scheme)['proof']

        if self.proving_scheme == 'gm17':
            return list(map(lambda x: int(x, 0), proof_data['a'] + proof_data['b'][0] + proof_data['b'][1] + proof_data['c']))
        else:
            raise NotImplementedError()
