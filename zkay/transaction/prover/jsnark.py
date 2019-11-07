import os
from tempfile import mkstemp
from typing import List

from zkay.jsnark_interface.libsnark_interface import libsnark_generate_proof
from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.interface import ZkayProverInterface


class JsnarkProver(ZkayProverInterface):
    def _generate_proof(self, verifier_dir: str, priv_values: List[int], in_vals: List[int], out_vals: List[int]) -> List[int]:
        args = list(map(int, priv_values + in_vals + out_vals))
        for arg in args:
            assert arg < bn128_scalar_field, 'argument overflow'

        with open(os.path.join(verifier_dir, 'circuit.in'), 'r') as f:
            input_wire_ids = f.readlines()
        input_wire_ids = [s.split(' ')[0] for s in input_wire_ids][1:]
        assert len(input_wire_ids) == len(args)

        _, infile = mkstemp('.in')
        with open(infile, 'w') as f:
            f.write('0 1\n')
            for idx in range(len(args)):
                f.write(f'{input_wire_ids[idx]} {hex(args[idx])[2:]}\n')

        cwd = os.getcwd()
        os.chdir(verifier_dir)
        libsnark_generate_proof(verifier_dir, infile, self.proving_scheme)
        os.chdir(cwd)
        os.remove(infile)

        with open(os.path.join(verifier_dir, 'proof.out')) as f:
            proof_lines = f.read().splitlines()
        proof = list(map(lambda x: int(x, 0), proof_lines))
        return proof
