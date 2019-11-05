default_proving_scheme = 'gm17'
default_snark_backend = 'jsnark'
pki_contract_name = 'PublicKeyInfrastructure'

zk_out_name = 'out__'
zk_in_name = 'in__'
zk_data_var_name = '__zk_data'
zk_param_name = f'{zk_data_var_name}_'

debug_output_whitelist = [
    #'jsnark',
    #'libsnark',
]

libsnark_check_verify_locally_during_proof_generation: bool = False


def should_use_hash(pub_arg_count: int):
    return True
