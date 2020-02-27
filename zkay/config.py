import math
from contextlib import contextmanager
from typing import Dict, Any, ContextManager

from zkay.compiler.privacy.proving_scheme.meta import provingschemeparams
from zkay.config_user import UserConfig
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


class Config(UserConfig):
    def __init__(self):
        super().__init__()

        # Internal values

        self._options_with_effect_on_circuit_output = [
            'proving_scheme', 'snark_backend', 'crypto_backend',
            'opt_solc_optimizer_runs', 'opt_hash_threshold',
            'opt_eval_constexpr_in_circuit', 'opt_cache_circuit_inputs', 'opt_cache_circuit_outputs',
        ]
        self._options_with_effect_if_not_empty = [
            'blockchain_pki_address', 'blockchain_bn256g2_address',
        ]

        self._is_unit_test = False

    def override_defaults(self, overrides: Dict[str, Any]):
        for arg, val in overrides.items():
            if not hasattr(self, arg):
                raise ValueError(f'Tried to override non-existing config value {arg}')
            setattr(self, arg, val)

    def export_compiler_settings(self) -> dict:
        out = {}
        for k in self._options_with_effect_on_circuit_output:
            out[k] = getattr(self, k)
        for k in self._options_with_effect_if_not_empty:
            if getattr(self, k):
                out[k] = getattr(self, k)
        return out

    def import_compiler_settings(self, vals: dict):
        for k in vals:
            if k not in self._options_with_effect_on_circuit_output and k not in self._options_with_effect_if_not_empty:
                raise KeyError(f'vals contains unknown option "{k}"')
            setattr(self, k, vals[k])

    @contextmanager
    def library_compilation_environment(self) -> ContextManager:
        """Use this fixed configuration compiling libraries to get reproducible output."""
        old_solc, old_opt_runs = self.solc_version, self.opt_solc_optimizer_runs
        self.override_solc('v0.5.16')
        self.opt_solc_optimizer_runs = 1000
        yield
        self.opt_solc_optimizer_runs = old_opt_runs
        self.override_solc(old_solc)

    @property
    def zkay_version(self) -> str:
        return '0.2'

    @property
    def solc_version(self) -> str:
        return 'v0.5.16'

    @staticmethod
    def override_solc(new_version):
        _init_solc(new_version)

    @property
    def key_bits(self) -> int:
        return cryptoparams[self.crypto_backend]['key_bits']

    @property
    def key_bytes(self) -> int:
        return self.key_bits // 8

    @property
    def rnd_bytes(self) -> int:
        return cryptoparams[self.crypto_backend]['rnd_bytes']

    @property
    def cipher_bytes_payload(self) -> int:
        return cryptoparams[self.crypto_backend]['cipher_payload_bytes']

    @property
    def cipher_bytes_meta(self) -> int:
        return cryptoparams[self.crypto_backend]['cipher_meta_bytes']

    def is_symmetric_cipher(self) -> bool:
        return cryptoparams[self.crypto_backend]['symmetric']

    @property
    def cipher_payload_len(self) -> int:
        return int(math.ceil(self.cipher_bytes_payload / self.cipher_chunk_size))

    @property
    def cipher_len(self) -> int:
        if self.is_symmetric_cipher():
            return self.cipher_payload_len + 1 # Additional uint to store sender address
        else:
            return self.cipher_payload_len

    @property
    def key_len(self) -> int:
        return 1 if self.is_symmetric_cipher() else int(math.ceil(self.key_bytes / self.cipher_chunk_size))

    @property
    def randomness_len(self) -> int:
        return 0 if self.is_symmetric_cipher() else int(math.ceil(self.rnd_bytes / self.rnd_chunk_size))

    @property
    def proof_len(self) -> int:
        return provingschemeparams[self.proving_scheme]['proof_len']

    def should_use_hash(self, circuit: 'CircuitHelper') -> bool:
        """
        This function determines whether input hashing is used for a particular circuit.

        :return: if true, all public circuit inputs are passed as private inputs into the circuit and only their combined hash-
                 value is passed as a public input. This makes verification constant-cost,
                 but increases offchain resource usage during key and proof generation.
        """

        pub_arg_size = circuit.trans_in_size + circuit.trans_out_size
        if self.is_unit_test:
            return pub_arg_size > self.opt_hash_threshold
        else:
            return True

    @property
    def reserved_name_prefix(self) -> str:
        return 'zk__'

    def get_internal_name(self, fct) -> str:
        if fct.requires_verification_when_external:
            return f'_{self.reserved_name_prefix}{fct.name}'
        else:
            return fct.name

    @staticmethod
    def get_contract_var_name(type_name: str) -> str:
        """
        Return an identifier referring to the address variable of verification contract of type 'type_name'

        :param type_name: name of the unqualified verification contract type
        :return: new identifier
        """
        return f'{type_name}_inst'

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
    def prover_key_hash_name(self) -> str:
        return f'{self.reserved_name_prefix}prover_key_hash'

    @property
    def zk_struct_prefix(self) -> str:
        return f'{self.reserved_name_prefix}data'

    @property
    def zk_data_var_name(self) -> str:
        return f'{self.zk_struct_prefix}'

    @property
    def jsnark_circuit_classname(self) -> str:
        return 'ZkayCircuit'

    @property
    def verification_function_name(self) -> str:
        return 'check_verify'

    @property
    def cipher_chunk_size(self) -> int:
        return cryptoparams[self.crypto_backend]['cipher_chunk_size']

    @property
    def rnd_chunk_size(self) -> int:
        return cryptoparams[self.crypto_backend]['rnd_chunk_size']

    @property
    def is_unit_test(self) -> bool:
        return self._is_unit_test


cfg = Config()
_init_solc(cfg.solc_version)
