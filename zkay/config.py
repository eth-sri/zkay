import json
import math
import os
from contextlib import contextmanager
from typing import Dict, Any, ContextManager, List, Optional

from semantic_version import NpmSpec, Version

from zkay.compiler.privacy.proving_scheme.meta import provingschemeparams
from zkay.config_user import UserConfig
from zkay.transaction.crypto.meta import cryptoparams


def zk_print(*args, verbose_only=False, **kwargs):
    if (not verbose_only or cfg.verbose) and not cfg.is_unit_test:
        print(*args, **kwargs)


def _init_solc(version):
    version_plain = version[1:] if version.startswith('v') else version

    import solcx
    if version == 'latest':
        concrete_version = solcx.install_solc_pragma(cfg.zkay_solc_version_compatibility.expression, install=False)
        if not version.startswith('v'):
            concrete_version = f'v{concrete_version}'
    else:
        try:
            semver = Version(version_plain)
        except ValueError:
            raise ValueError(f'Invalid version string {version}')

        if semver not in cfg.zkay_solc_version_compatibility:
            raise ValueError(f'Solidity version {version} is not supported by zkay {cfg.zkay_version} (requires solc {cfg.zkay_solc_version_compatibility.expression})')
        concrete_version = f'v{version_plain}'

    if concrete_version not in solcx.get_installed_solc_versions():
        assert concrete_version in solcx.get_available_solc_versions()
        solcx.install_solc(concrete_version)

    assert concrete_version in solcx.get_installed_solc_versions()
    cfg._concrete_solc_version = concrete_version
    solcx.set_solc_version(concrete_version, silent=True)


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
            'blockchain_pki_address', 'blockchain_crypto_lib_addresses',
        ]

        self._is_unit_test = False
        self._concrete_solc_version = None

    def load_configuration_from_disk(self, local_cfg_file: str):
        # Load global configuration file
        global_config_dir = self._appdirs.site_config_dir
        global_cfg_file = os.path.join(global_config_dir, 'config.json')
        if os.path.exists(global_cfg_file):
            with open(global_cfg_file) as conf:
                self.override_defaults(json.load(conf))

        # Load user configuration file
        user_config_dir = self._appdirs.user_config_dir
        user_cfg_file = os.path.join(user_config_dir, 'config.json')
        if os.path.exists(user_cfg_file):
            with open(user_cfg_file) as conf:
                self.override_defaults(json.load(conf))

        # Load local configuration file
        if os.path.exists(local_cfg_file):
            with open(local_cfg_file) as conf:
                self.override_defaults(json.load(conf))

    def override_defaults(self, overrides: Dict[str, Any]):
        # TODO validate override values (check whether they have legal values for the respective config option)
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
        """zkay version number"""
        return '0.2.0'

    @property
    def zkay_solc_version_compatibility(self) -> NpmSpec:
        """Target solidity language level for the current zkay version"""
        return NpmSpec('^0.5.0')

    @property
    def solc_version(self) -> str:
        assert self._concrete_solc_version is not None and self._concrete_solc_version != 'latest'
        return self._concrete_solc_version

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

    @property
    def external_crypto_lib_names(self) -> List[str]:
        """Names of all solidity libraries in verify_libs.sol, which need to be linked against."""
        return provingschemeparams[self.proving_scheme]['external_sol_libs']

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
        """
        Identifiers in user code must not start with this prefix.

        This is to ensure that user code does not interfere with the additional code generated by the zkay compiler.
        """
        return 'zk__'

    @property
    def reserved_conflict_resolution_suffix(self) -> str:
        """
        Identifiers in user code must not end with this suffix.

        This is used for resolving conflicts with python globals in the generated offchain simulation code.
        """
        return '_zalt'

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
_init_solc('latest')
