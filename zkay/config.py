import ast
import math
import os
from typing import Dict

import solcx

from zkay.compiler.privacy.proving_schemes.meta import provingschemeparams
from zkay.transaction.crypto.meta import cryptoparams


# Set solc version (and automatically install if missing)
SOLC_VERSION = 'v0.5.13'
if SOLC_VERSION not in solcx.get_installed_solc_versions():
    assert SOLC_VERSION in solcx.get_available_solc_versions()
    solcx.install_solc(SOLC_VERSION, allow_osx=True)
solcx.set_solc_version(SOLC_VERSION)
assert SOLC_VERSION in solcx.get_installed_solc_versions()

__debug_print = True


def debug_print(*args, **kwargs):
    if __debug_print and not cfg.is_unit_test:
        print(*args, **kwargs)


class Config:
    def __init__(self):
        self.config_dir = os.path.dirname(os.path.realpath(__file__))

        self.is_unit_test = False
        self.use_circuit_cache_during_testing_with_encryption = True

        # proving scheme to use for nizk proof [gm17]
        self.proving_scheme = 'gm17'
        # prover backend [jsnark]
        self.snark_backend = 'jsnark'
        # encryption algorithm [dummy, rsa_pkcs1_5, rsa_oaep]
        self.crypto_backend = 'dummy'

        self.indentation = ' '*4

        self.jsnark_circuit_classname = 'ZkayCircuit'
        self.pki_contract_name = 'PublicKeyInfrastructure'

        self.zk_out_name = 'out__'
        self.zk_in_name = 'in__'
        self.zk_struct_suffix = 'zk_data'
        self.return_var_name = 'return_value__'
        self.proof_param_name = 'proof__'
        self.verification_function_name = 'check_verify'

        self.pack_chunk_size = 31

        self.debug_output_whitelist = {
            'jsnark',
            'libsnark',
        }

        self.libsnark_check_verify_locally_during_proof_generation: bool = False

    def override_defaults(self, overrides: Dict[str, str]):
        for arg, val in overrides.items():
            if not hasattr(self, arg):
                raise ValueError(f'Tried to override non-existing config value {arg}')
            setattr(self, arg, ast.literal_eval(val))

    @property
    def zk_data_var_name(self):
        return f'{self.zk_struct_suffix}__'

    @property
    def key_bits(self):
        return cryptoparams[self.crypto_backend]['key_bits']

    @property
    def key_bytes(self):
        return self.key_bits // 8

    @property
    def rnd_bytes(self):
        return cryptoparams[self.crypto_backend]['rnd_bytes']

    @property
    def cipher_len(self):
        return int(math.ceil(self.key_bytes / self.pack_chunk_size))

    @property
    def key_len(self):
        return int(math.ceil(self.key_bytes / self.pack_chunk_size))

    @property
    def randomness_len(self):
        return int(math.ceil(self.rnd_bytes / self.pack_chunk_size))

    @property
    def proof_len(self):
        return provingschemeparams[self.proving_scheme]['proof_len']

    def should_use_hash(self, pub_arg_size: int):
        if self.is_unit_test:
            return pub_arg_size > 70
        else:
            return True

    def get_internal_name(self, fct) -> str:
        if fct.requires_verification_when_external:
            return f'_{fct.name}'
        else:
            return fct.name


cfg = Config()
