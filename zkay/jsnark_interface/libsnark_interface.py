import os

from zkay.config import cfg
from zkay.utils.run_command import run_command

libsnark_runner = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'run_snark')

proving_scheme_map = {
    'pghr13': 0,
    'groth16': 1,
    'gm17': 2
}


def generate_keys(input_dir: str, output_dir: str, proving_scheme: str):
    """
    Generate prover and verification keys for the circuit in output_dir with the specified proving_scheme.

    :param input_dir: path to directory where the circuit.arith and .in files are located
    :param output_dir: path to the directory where the keys should be saved
    :param proving_scheme: name of the proving scheme to use
    :raise SubprocessError: if key generation fails
    :raise KeyError: if proving scheme name is invalid
    """
    run_command([libsnark_runner, 'keygen', input_dir, output_dir, str(proving_scheme_map[proving_scheme])], allow_verbose=True)


def generate_proof(key_dir: str, input_dir: str, output_path: str, proving_scheme: str):
    """
    Generate a NIZK-proof for the circuit and input files in output_dir.

    :param key_dir: directory where proving.key and verifying.key.bin are located
    :param input_dir: directory where circuit.arith and circuit.in for this circuit are located.
    :param output_path: output path for the generated proof file
    :param proving_scheme: name of the proving scheme to use
    :raise SubprocessError: if proof generation fails
    :raise KeyError: if proving scheme name is invalid
    """
    run_command([libsnark_runner, 'proofgen', input_dir, output_path, key_dir, str(proving_scheme_map[proving_scheme]),
                 str(int(cfg.libsnark_check_verify_locally_during_proof_generation))], allow_verbose=True)
