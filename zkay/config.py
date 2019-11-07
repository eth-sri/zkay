import math
import os
config_dir = os.path.dirname(os.path.realpath(__file__))

default_proving_scheme = 'gm17'
default_snark_backend = 'jsnark'
pki_contract_name = 'PublicKeyInfrastructure'

zk_out_name = 'out__'
zk_in_name = 'in__'
zk_struct_suffix = 'zk_data'
zk_data_var_name = f'{zk_struct_suffix}__'

rsa_key_bits = 256
rsa_key_bytes = rsa_key_bits // 8
rsa_rnd_bytes = 32 # sha256 digest size = 256bit
pack_chunk_size = 30

cipher_len = int(math.ceil(rsa_key_bytes / pack_chunk_size))
key_len = int(math.ceil(rsa_key_bytes / pack_chunk_size))
randomness_len = int(math.ceil(rsa_rnd_bytes / pack_chunk_size))
proof_len = 8

debug_output_whitelist = [
    #'jsnark',
    #'libsnark',
]

libsnark_check_verify_locally_during_proof_generation: bool = False


def should_use_hash(pub_arg_count: int):
    return True
