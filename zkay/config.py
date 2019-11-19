import math
import os
from zkay.transaction.crypto.meta import cryptoparams
from zkay.compiler.privacy.proving_schemes.meta import provingschemeparams

config_dir = os.path.dirname(os.path.realpath(__file__))

# proving scheme to use for nizk proof [gm17]
proving_scheme = 'gm17'
# prover backend [zokrates, jsnark]
snark_backend = 'jsnark'
# encryption algorithm [dummy, rsa_pkcs1_5, rsa_oaep]
crypto_backend = 'dummy'

generate_offchain_circuit_simulation_code = False
indentation = ' '*4

pki_contract_name = 'PublicKeyInfrastructure'
jsnark_circuit_classname = 'ZkayCircuit'

zk_out_name = 'out__'
zk_in_name = 'in__'
zk_struct_suffix = 'zk_data'
zk_data_var_name = f'{zk_struct_suffix}__'
return_var_name = 'return_value__'

pack_chunk_size = 31
key_bits = cryptoparams[crypto_backend]['key_bits']
key_bytes = key_bits // 8
rnd_bytes = cryptoparams[crypto_backend]['rnd_bytes']

cipher_len = int(math.ceil(key_bytes / pack_chunk_size))
key_len = int(math.ceil(key_bytes / pack_chunk_size))
randomness_len = int(math.ceil(rnd_bytes / pack_chunk_size))

proof_len = provingschemeparams[proving_scheme]['proof_len']

debug_output_whitelist = [
    'jsnark',
    'libsnark',
]

libsnark_check_verify_locally_during_proof_generation: bool = False


def should_use_hash(pub_arg_count: int):
    return True
