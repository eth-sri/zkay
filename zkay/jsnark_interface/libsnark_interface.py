import os

from zkay.config import cfg
from zkay.utils.run_command import run_command

libsnark_runner = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'run_snark')

proving_scheme_map = {
    'gm17': 0
}


def generate_keys(output_dir: str, proving_scheme: str):
    """
    Generate prover and verification keys for the circuit in output_dir with the specified proving_scheme.

    :param output_dir: path to directory where the circuit.arith and .in files are located
    :param proving_scheme: name of the proving scheme to use
    :raise SubprocessError: if key generation fails
    :raise KeyError: if proving scheme name is invalid
    """
    run_command([libsnark_runner, 'keygen', str(proving_scheme_map[proving_scheme])], cwd=output_dir, allow_verbose=True)


def generate_proof(output_dir: str, proving_scheme: str):
    """
    Generate a NIZK-proof for the circuit and input files in output_dir.

    :param output_dir: directory where the proving.key, circuit.arith and circuit.in for this circuit are located.
    :param proving_scheme: name of the proving scheme to use
    :raise SubprocessError: if proof generation fails
    :raise KeyError: if proving scheme name is invalid
    """
    run_command([libsnark_runner, 'proofgen', str(proving_scheme_map[proving_scheme]),
                 str(int(cfg.libsnark_check_verify_locally_during_proof_generation))], cwd=output_dir, allow_verbose=True)
