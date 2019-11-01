import ctypes
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
snark_interface = ctypes.CDLL(os.path.join(dir_path, 'libzkay_snark_interface.so'))

proving_scheme_map = {
    'gm17': 0
}


def libsnark_generate_keys(output_dir: str, proving_scheme: str):
    ret = snark_interface.generate_keys(ctypes.c_char_p(output_dir.encode('utf-8')), proving_scheme_map[proving_scheme])
    if ret != 0:
        raise RuntimeError("Snark interface execution failed")


def libsnark_generate_proof(output_dir: str, input_map, proving_scheme: str):
    ret = snark_interface.generate_proof(ctypes.c_char_p(output_dir.encode('utf-8')), ctypes.c_char_p(''.encode('utf-8')), proving_scheme_map[proving_scheme])
    if ret != 0:
        raise RuntimeError("Snark interface execution failed")
