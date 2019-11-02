default_proving_scheme = 'gm17'
default_snark_backend = 'jsnark'
pki_contract_name = 'PublicKeyInfrastructure'

debug_output_whitelist = [
    #'jsnark',
    #'libsnark',
]

libsnark_check_verify_locally_during_proof_generation: bool = False


def should_use_hash(pub_arg_count: int):
    return True
