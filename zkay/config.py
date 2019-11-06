default_proving_scheme = 'gm17'
default_snark_backend = 'jsnark'
pki_contract_name = 'PublicKeyInfrastructure'

zk_out_name = 'out__'
zk_in_name = 'in__'
zk_struct_suffix = 'zk_data'
zk_data_var_name = f'{zk_struct_suffix}__'

cipher_len = 2
key_len = 2
randomness_len = 2
proof_len = 8

debug_output_whitelist = [
    #'jsnark',
    #'libsnark',
]

libsnark_check_verify_locally_during_proof_generation: bool = False


def should_use_hash(pub_arg_count: int):
    return True
