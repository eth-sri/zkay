import os
from pathlib import Path
from typing import List, Dict, Union

import zkay.jsnark_interface.jsnark_interface as jsnark
import zkay.jsnark_interface.libsnark_interface as libsnark
from zkay.transaction.interface import ZkayProverInterface
from zkay.utils.timer import time_measure


class JsnarkProver(ZkayProverInterface):
    def _generate_proof(self, verifier_dir: str, priv_values: Dict[str, Union[List[int]]], in_vals: List[int], out_vals: List[int]) -> List[int]:
        pub_args = list(map(int, in_vals + out_vals))
        for key, vals in priv_values.items():
            priv_values[key] = list(map(int, vals))

        with time_measure("jsnark_prepare_proof_" + Path(verifier_dir).name):
            jsnark.prepare_proof(verifier_dir, pub_args, priv_values)

        with time_measure("libsnark_gen_proof_" + Path(verifier_dir).name):
            libsnark.generate_proof(verifier_dir, self.proving_scheme)

        with open(os.path.join(verifier_dir, 'proof.out')) as f:
            proof_lines = f.read().splitlines()
        proof = list(map(lambda x: int(x, 0), proof_lines))
        return proof
