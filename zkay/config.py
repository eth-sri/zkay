import ast
import math
import os
from typing import Dict

from zkay.compiler.privacy.proving_schemes.meta import provingschemeparams
from zkay.transaction.crypto.meta import cryptoparams


class Config:
    def __init__(self):
        self.config_dir = os.path.dirname(os.path.realpath(__file__))

        self.is_unit_test = False

        # proving scheme to use for nizk proof [gm17]
        self.proving_scheme = 'gm17'
        # prover backend [zokrates, jsnark]
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
