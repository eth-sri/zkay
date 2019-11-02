import ctypes
import os

from zkay.config import libsnark_check_verify_locally_during_proof_generation
from zkay.utils.output_suppressor import output_suppressed

dir_path = os.path.dirname(os.path.realpath(__file__))
snark_interface = ctypes.CDLL(os.path.join(dir_path, 'libzkay_snark_interface.so'))

proving_scheme_map = {
    'gm17': 0
}


def libsnark_generate_keys(output_dir: str, proving_scheme: str):
    with output_suppressed('libsnark'):
        ret = snark_interface.generate_keys(ctypes.c_char_p(output_dir.encode('utf-8')), proving_scheme_map[proving_scheme])
    if ret != 0:
        raise RuntimeError("Error during key generation")


def libsnark_generate_proof(output_dir: str, input_filename: str, proving_scheme: str):
    with output_suppressed('libsnark'):
        ret = snark_interface.generate_proof(ctypes.c_char_p(output_dir.encode('utf-8')),
                                             ctypes.c_char_p(input_filename.encode('utf-8')),
                                             proving_scheme_map[proving_scheme],
                                             int(libsnark_check_verify_locally_during_proof_generation))
    if ret != 0:
        raise RuntimeError("Error during proof generation?")
