import os
from subprocess import SubprocessError
from tempfile import TemporaryDirectory
from typing import List

import zkay.jsnark_interface.jsnark_interface as jsnark
import zkay.jsnark_interface.libsnark_interface as libsnark
from zkay.config import cfg
from zkay.transaction.interface import ZkayProverInterface, ProofGenerationError
from zkay.utils.helpers import hash_file
from zkay.utils.timer import time_measure


class JsnarkProver(ZkayProverInterface):
    def _generate_proof(self, verifier_dir: str, priv_values: List[int], in_vals: List[int], out_vals: List[int]) -> List[int]:
        args = list(map(int, in_vals + out_vals + priv_values))

        # Generate proof in temporary directory
        with TemporaryDirectory() as tempd:
            # Symlink circuit and key files into the directory
            files = [f'{cfg.jsnark_circuit_classname}.class', 'proving.key', 'verification.key.bin']
            for file in files:
                os.symlink(os.path.join(verifier_dir, file), os.path.join(tempd, file))

            try:
                with time_measure("jsnark_prepare_proof"):
                    jsnark.prepare_proof(tempd, args)

                with time_measure("libsnark_gen_proof"):
                    libsnark.generate_proof(tempd, self.proving_scheme)
            except SubprocessError as e:
                raise ProofGenerationError(e.args)

            with open(os.path.join(tempd, 'proof.out')) as f:
                proof_lines = f.read().splitlines()
        proof = list(map(lambda x: int(x, 0), proof_lines))
        return proof

    def get_prover_key_hash(self, verifier_directory: str) -> bytes:
        return hash_file(os.path.join(verifier_directory, 'proving.key'))
