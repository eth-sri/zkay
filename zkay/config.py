import ast
import math
from contextlib import contextmanager
from typing import Dict, Any, Optional, Union, ContextManager

import appdirs

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
        # User configuration

        self.proving_scheme = 'gm17'
        """NIZK proving scheme to use [gm17]"""

        self.snark_backend = 'jsnark'
        """Snark backend to use [jsnark]"""

        self.crypto_backend = 'dummy'
        """Encryption backend to use [dummy, rsa-pkcs1.5, rsa-oaep]"""

        self.blockchain_backend = 'w3-eth-tester'
        """
        Backend to use when interacting with the blockchain [w3-eth-tester, w3-ganache, w3-ipc, w3-websocket, w3-http, w3-custom]
        Running unit tests is only supported with w3-eth-tester and w3-ganache at the moment (because they need pre-funded dummy accounts).
        See https://web3py.readthedocs.io/en/stable/providers.html for more information
        """

        self.blockchain_node_uri: Optional[Any] = 'http://localhost:7545'
        """
        Backend specific location of the ethereum node
        w3-eth-tester : unused
        w3-ganache    : url
        w3-ipc        : path to ipc socket file
        w3-websocket  : web socket uri
        w3-http       : url
        w3-custom     : web3 instance, must not be None
        """

        self.blockchain_pki_address: str = ''
        """Address of the deployed pki contract, if empty, the pki contract will be deployed on startup (for debugging)"""

        self.blockchain_bn256g2_address: str = ''
        """Address of the deployed bn256 contract, if empty, the library will be deployed on startup (for debugging)"""

        self.blockchain_default_account: Union[int, str, None] = 0
        """
        Address of the wallet which should be used when no sender is specified.
        (will also be used to deploy the pki contract when no pki_address is specified)

        If None -> must always specify a sender, empty blockchain_pki_address is invalid
        If int -> use eth.accounts[int]
        If str -> use address str
        """

        self.indentation = ' '*4
        """Specifies the identation which should be used for the generated code output."""

        self.libsnark_check_verify_locally_during_proof_generation: bool = False
        """If true, the libsnark interface verifies locally whether the proof can be verified during proof generation."""

        self.debug_output_whitelist = {
            'jsnark',
            'libsnark',
        }
        """
        If the 'key' argument of run_command matches an entry in this list, the commands output directly goes to stdout
        instead of being captured. -> Useful for debugging, but must not specify a key if output capturing is required.
        """

        self.opt_solc_optimizer_runs = 50
        """SOLC: optimize for how many times to run the code"""

        self.opt_hash_threshold = 70
        """
        If there are more than this many public circuit inputs (in uints), the hashing optimization will be used
        (only the hash of all public inputs will be passed as public input, public inputs are passed as private circuit inputs and
        the circuit verifies that the hash matches to ensure correctness)

        When hashing is enabled -> cheaper on-chain costs for verification (O(1) in #public args instead of O(n)),
        but much higher off-chain costs (key and proof generation time, memory consumption).
        """

        self.opt_eval_constexpr_in_circuit = True
        """
        If true, literal expressions are folded and the result is baked into the circuit as a constant
        (as opposed to being evaluated outside the circuit and the result being moved in as an additional circuit input)
        """

        self.opt_cache_circuit_inputs = True
        """
        If true, identifier circuit inputs will be cached (i.e. if an identifier is referenced multiple times within a private expression,
        or multiple times in different private expressions without being publicly written to in between,
        then the identifier will only be added to the circuit inputs once and all private uses will share the same input variable.
        """

        self.opt_cache_circuit_outputs = True
        """
        Normally, the value cached in the circuit for a particular identifier must be invalidated whenever the identifier is
        assigned to in public code.

        If this optimization is enabled, assignments where the lhs is an Identifier and the rhs is a private expression
        will update the cached value stored in the circuit instead of invalidating it. (since updated value == private expression result,
        the corresponding plaintext value is already available in the circuit)
        """

        # Internal values

        self._options_with_effect_on_circuit_output = [
            'proving_scheme', 'snark_backend', 'crypto_backend',
            'opt_solc_optimizer_runs', 'opt_hash_threshold',
            'opt_eval_constexpr_in_circuit', 'opt_cache_circuit_inputs', 'opt_cache_circuit_outputs',
        ]
        self._options_with_effect_if_not_empty = [
            'blockchain_pki_address', 'blockchain_bn256g2_address',
        ]
        self.config_dir = appdirs.user_config_dir('zkay', False, None, True)
        self.data_dir = appdirs.user_data_dir('zkay', False, None, True)
        self.is_unit_test = False
        self.use_circuit_cache_during_testing_with_encryption = True

    def override_defaults(self, overrides: Dict[str, str]):
        for arg, val in overrides.items():
            if not hasattr(self, arg):
                raise ValueError(f'Tried to override non-existing config value {arg}')
            setattr(self, arg, ast.literal_eval(val))

    def serialize(self) -> dict:
        out = {}
        for k in self._options_with_effect_on_circuit_output:
            out[k] = getattr(self, k)
        for k in self._options_with_effect_if_not_empty:
            if getattr(self, k):
                out[k] = getattr(self, k)
        return out

    def deserialize(self, vals: dict):
        for k in vals:
            if k not in self._options_with_effect_on_circuit_output and k not in self._options_with_effect_if_not_empty:
                raise KeyError(f'vals contains unknown option "{k}"')
            setattr(self, k, vals[k])

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
    def zk_data_var_name(self):
        return f'{self.zk_struct_prefix}'

    @property
    def jsnark_circuit_classname(self) -> str:
        return 'ZkayCircuit'

    @property
    def verification_function_name(self) -> str:
        return 'check_verify'

    @property
    def pack_chunk_size(self) -> int:
        return 31


cfg = Config()
_init_solc(cfg.solc_version)
