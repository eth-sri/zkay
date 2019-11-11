import os

from zkay.config import libsnark_check_verify_locally_during_proof_generation
from zkay.utils.output_suppressor import output_suppressed
from zkay.utils.run_command import run_command

libsnark_runner = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'run_snark')

proving_scheme_map = {
    'gm17': 0
}


def generate_keys(output_dir: str, proving_scheme: str):
    with output_suppressed('libsnark'):
        out, err = run_command([libsnark_runner, 'keygen', str(proving_scheme_map[proving_scheme])], cwd=output_dir)
        print(out, err)


def generate_proof(output_dir: str, proving_scheme: str):
    with output_suppressed('libsnark'):
        out, err = run_command([libsnark_runner, 'proofgen', str(proving_scheme_map[proving_scheme]),
                                str(int(libsnark_check_verify_locally_during_proof_generation))], cwd=output_dir)
        print(out, err)
