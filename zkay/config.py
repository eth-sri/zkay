import ast
import math
import os
from typing import Dict

from zkay.compiler.privacy.proving_scheme.meta import provingschemeparams
from zkay.transaction.crypto.meta import cryptoparams

__debug_print = True
def debug_print(*args, **kwargs):
    if __debug_print and not cfg.is_unit_test:
        print(*args, **kwargs)


def _init_solc(version):
    if not version.startswith('v0.5'):
        raise ValueError('Currently only solc 0.5 is supported.')

    import solcx
    if version not in solcx.get_installed_solc_versions():
        assert version in solcx.get_available_solc_versions()
        solcx.install_solc(version, allow_osx=True)
    solcx.set_solc_version(version)
    assert version in solcx.get_installed_solc_versions()


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

        self.reserved_name_prefix = 'zk__'
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
    def zkay_version(self):
        return '0.2'

    @property
    def solc_version(self):
        return 'v0.5.16'

    @staticmethod
    def override_solc(new_version):
        _init_solc(new_version)

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

    def should_use_hash(self, circuit: 'CircuitHelper'):
        """
        This function determines whether input hashing is used for a particular circuit.

        :return: if true, all public circuit inputs are passed as private inputs into the circuit and only their combined hash-
                 value is passed as a public input. This makes verification constant-cost,
                 but increases offchain resource usage during key and proof generation.
        """

        pub_arg_size = circuit.trans_in_size + circuit.trans_out_size
        if self.is_unit_test:
            return pub_arg_size > 70
        else:
            return True

    def get_internal_name(self, fct) -> str:
        if fct.requires_verification_when_external:
            return f'_{self.reserved_name_prefix}{fct.name}'
        else:
            return fct.name

    @property
    def pki_contract_name(self) -> str:
        return f'{self.reserved_name_prefix}PublicKeyInfrastructure'

    @property
    def zk_out_name(self) -> str:
        return f'{self.reserved_name_prefix}out'

    @property
    def zk_in_name(self) -> str:
        return f'{self.reserved_name_prefix}in'

    @property
    def proof_param_name(self) -> str:
        return f'{self.reserved_name_prefix}proof'

    @property
    def return_var_name(self) -> str:
        return f'{self.reserved_name_prefix}ret'

    @property
    def field_prime_var_name(self) -> str:
        return f'{self.reserved_name_prefix}field_prime'

    @property
    def zk_struct_prefix(self) -> str:
        return f'{self.reserved_name_prefix}data'

    @property
    def zk_data_var_name(self):
        return f'{self.zk_struct_prefix}'


cfg = Config()
_init_solc(cfg.solc_version)
