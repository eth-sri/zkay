"""
This module defines the zkay options which are configurable by the user via command line arguments.

The argument parser in :py:mod:`.__main__` uses the docstrings, type hints and _values for the help
 strings and the _values fields for autocompletion

WARNING: This is one of the only zkay modules that is imported before argcomplete.autocomplete is called. \
For performance reasons it should thus not have any import side-effects or perform any expensive operations during import.
"""
from typing import Any, Union, Dict, List

from appdirs import AppDirs

from zkay.transaction.crypto.params import CryptoParams
from zkay.zkay_ast.homomorphism import Homomorphism


def _check_is_one_of(val: str, legal_vals):
    if val not in legal_vals:
        raise ValueError(f'Invalid config value {val}, must be one of {legal_vals}')


def _type_check(val: Any, t):
    if not isinstance(val, t):
        raise ValueError(f'Value {val} has wrong type (expected {t})')


class UserConfig:
    def __init__(self):
        self._appdirs = AppDirs('zkay', appauthor=False, version=None, roaming=True)

        # User configuration
        # Each attribute must have a type hint and a docstring for correct help strings in the commandline interface.
        # If 'Available Options: [...]' is specified, the options are used for autocomplete suggestions.

        # Global defaults
        self._proving_scheme: str = 'groth16'
        self._proving_scheme_values = ['groth16', 'gm17']

        self._snark_backend: str = 'jsnark'
        self._snark_backend_values = ['jsnark']

        self._main_crypto_backend_values = ['dummy', 'dummy-hom', 'rsa-pkcs1.5', 'rsa-oaep', 'ecdh-aes', 'ecdh-chaskey', 'paillier']  # TODO
        self._crypto_backends: Dict[Homomorphism, str] = {
            Homomorphism.NON_HOMOMORPHIC: 'ecdh-aes',
            Homomorphism.ADDITIVE: 'paillier'
        }
        self._crypto_backend_values: Dict[Homomorphism, List[str]] = {
            Homomorphism.NON_HOMOMORPHIC: ['dummy', 'rsa-pkcs1.5', 'rsa-oaep', 'ecdh-aes', 'ecdh-chaskey', 'paillier'],
            Homomorphism.ADDITIVE: ['dummy-hom', 'paillier']
        }

        self._blockchain_backend: str = 'w3-eth-tester'
        self._blockchain_backend_values = ['w3-eth-tester', 'w3-ganache', 'w3-ipc', 'w3-websocket', 'w3-http', 'w3-custom']

        self._blockchain_node_uri: Union[Any, str, None] = 'http://localhost:7545'
        self._blockchain_pki_address: str = ''
        self._blockchain_crypto_lib_addresses: str = ''
        self._blockchain_default_account: Union[int, str, None] = 0

        self._indentation: str = ' ' * 4
        self._libsnark_check_verify_locally_during_proof_generation: bool = False

        self._opt_solc_optimizer_runs: int = 50
        self._opt_hash_threshold: int = 1
        self._opt_eval_constexpr_in_circuit: bool = True
        self._opt_cache_circuit_inputs: bool = True
        self._opt_cache_circuit_outputs: bool = True

        self._data_dir: str = self._appdirs.user_data_dir
        self._log_dir: str = self._appdirs.user_log_dir
        self._use_circuit_cache_during_testing_with_encryption: bool = True
        self._verbosity: int = 1

    @property
    def proving_scheme(self) -> str:
        """
        NIZK proving scheme to use.

        Available Options: [gm17]
        """
        return self._proving_scheme

    @proving_scheme.setter
    def proving_scheme(self, val: str):
        _check_is_one_of(val, self._proving_scheme_values)
        self._proving_scheme = val

    @property
    def snark_backend(self) -> str:
        """
        Snark backend to use.

        Available Options: [jsnark]
        """
        return self._snark_backend

    @snark_backend.setter
    def snark_backend(self, val: str):
        _check_is_one_of(val, self._snark_backend_values)
        self._snark_backend = val

    @property
    def main_crypto_backend(self) -> str:
        """
        Main encryption backend to use.

        Available Options: [dummy, rsa-pkcs1.5, rsa-oaep, ecdh-aes, ecdh-chaskey, paillier]
        """
        return self.get_crypto_backend(Homomorphism.NON_HOMOMORPHIC)

    @main_crypto_backend.setter
    def main_crypto_backend(self, val: str):
        self.set_crypto_backend(Homomorphism.NON_HOMOMORPHIC, val)

    @property
    def addhom_crypto_backend(self) -> str:
        """
        Additively homomorphic encryption backend to use.

        Available Options: [dummy-hom, paillier]
        """
        return self.get_crypto_backend(Homomorphism.ADDITIVE)

    @addhom_crypto_backend.setter
    def addhom_crypto_backend(self, val: str):
        self.set_crypto_backend(Homomorphism.ADDITIVE, val)

    def get_crypto_backend(self, hom: Homomorphism) -> str:
        return self._crypto_backends[hom]

    def set_crypto_backend(self, hom: Homomorphism, val: str):
        _check_is_one_of(val, self._crypto_backend_values[hom])
        self._crypto_backends[hom] = val

    def get_crypto_params(self, hom: Homomorphism) -> CryptoParams:
        return CryptoParams(self.get_crypto_backend(hom))

    @property
    def blockchain_backend(self) -> str:
        """
        Backend to use when interacting with the blockchain.

        Running unit tests is only supported with w3-eth-tester and w3-ganache at the moment (because they need pre-funded dummy accounts).
        See https://web3py.readthedocs.io/en/stable/providers.html for more information.

        Available Options: [w3-eth-tester, w3-ganache, w3-ipc, w3-websocket, w3-http, w3-custom]
        """
        return self._blockchain_backend

    @blockchain_backend.setter
    def blockchain_backend(self, val: str):
        _check_is_one_of(val, self._blockchain_backend_values)
        self._blockchain_backend = val

    @property
    def blockchain_node_uri(self) -> Union[Any, str, None]:
        """
        Backend specific location of the ethereum node
        w3-eth-tester : unused
        w3-ganache    : url
        w3-ipc        : path to ipc socket file
        w3-websocket  : web socket uri
        w3-http       : url
        w3-custom     : web3 instance, must not be None
        """
        return self._blockchain_node_uri

    @blockchain_node_uri.setter
    def blockchain_node_uri(self, val: Union[Any, str, None]):
        self._blockchain_node_uri = val

    @property
    def blockchain_pki_address(self) -> str:
        """
        Address of the deployed pki contract.

        Must be specified for backends other than w3-eth-tester.
        This library can be deployed using ``zkay deploy-pki``.
        """
        return self._blockchain_pki_address

    @blockchain_pki_address.setter
    def blockchain_pki_address(self, val: str):
        _type_check(val, str)
        self._blockchain_pki_address = val

    @property
    def blockchain_crypto_lib_addresses(self) -> str:
        """
        Comma separated list of the addresses of the deployed crypto library contracts required for the current proving_scheme.
        e.g. "0xAb31...,0xec32C..."

        Must be specified for backends other than w3-eth-tester.
        The libraries can be deployed using ``zkay deploy-crypto-libs``.
        The addresses in the list must appear in the same order as the corresponding
        libraries were deployed by that command.
        """
        return self._blockchain_crypto_lib_addresses

    @blockchain_crypto_lib_addresses.setter
    def blockchain_crypto_lib_addresses(self, val: str):
        _type_check(val, str)
        self._blockchain_crypto_lib_addresses = val

    @property
    def blockchain_default_account(self) -> Union[int, str, None]:
        """
        Address of the wallet which should be made available under the name 'me' in contract.py.

        If None -> must always specify a sender, empty blockchain_pki_address is invalid
        If int -> use eth.accounts[int]
        If str -> use address str
        """
        return self._blockchain_default_account

    @blockchain_default_account.setter
    def blockchain_default_account(self, val: str):
        _type_check(val, (int, str, None))
        self._blockchain_default_account = val

    @property
    def indentation(self) -> str:
        """Specifies the identation which should be used for the generated code output."""
        return self._indentation

    @indentation.setter
    def indentation(self, val: str):
        _type_check(val, str)
        self._indentation = val

    @property
    def libsnark_check_verify_locally_during_proof_generation(self) -> bool:
        """
        If true, the libsnark interface verifies locally whether the proof can be verified during proof generation."""
        return self._libsnark_check_verify_locally_during_proof_generation

    @libsnark_check_verify_locally_during_proof_generation.setter
    def libsnark_check_verify_locally_during_proof_generation(self, val: bool):
        _type_check(val, bool)
        self._libsnark_check_verify_locally_during_proof_generation = val

    @property
    def opt_solc_optimizer_runs(self) -> int:
        """SOLC: optimize for how many times to run the code"""
        return self._opt_solc_optimizer_runs

    @opt_solc_optimizer_runs.setter
    def opt_solc_optimizer_runs(self, val: int):
        _type_check(val, int)
        self._opt_solc_optimizer_runs = val

    @property
    def opt_hash_threshold(self) -> int:
        """
        If there are more than this many public circuit inputs (in uints), the hashing optimization will be enabled.

        This means that only the hash of all public inputs will be passed as public input,
        public inputs are passed as private circuit inputs and the circuit verifies
        that the hash matches to ensure correctness.

        When hashing is enabled -> cheaper on-chain costs for verification (O(1) in #public args instead of O(n)),
        but much higher off-chain costs (key and proof generation time, memory consumption).
        """
        return self._opt_hash_threshold

    @opt_hash_threshold.setter
    def opt_hash_threshold(self, val: int):
        _type_check(val, int)
        self._opt_hash_threshold = val

    @property
    def opt_eval_constexpr_in_circuit(self) -> bool:
        """
        If true, literal expressions are folded and the result is baked into the circuit as a constant
        (as opposed to being evaluated outside the circuit and the result being moved in as an additional circuit input)
        """
        return self._opt_eval_constexpr_in_circuit

    @opt_eval_constexpr_in_circuit.setter
    def opt_eval_constexpr_in_circuit(self, val: bool):
        _type_check(val, bool)
        self._opt_eval_constexpr_in_circuit = val

    @property
    def opt_cache_circuit_inputs(self) -> bool:
        """
        If true, identifier circuit inputs will be cached
        (i.e. if an identifier is referenced multiple times within a private expression,
        or multiple times in different private expressions without being publicly written to in between,
        then the identifier will only be added to the circuit inputs once and all private
        uses will share the same input variable.
        """
        return self._opt_cache_circuit_inputs

    @opt_cache_circuit_inputs.setter
    def opt_cache_circuit_inputs(self, val: bool):
        _type_check(val, bool)
        self._opt_cache_circuit_inputs = val

    @property
    def opt_cache_circuit_outputs(self) -> bool:
        """
        Normally, the value cached in the circuit for a particular identifier must be invalidated whenever the
        identifier is assigned to in public code.

        If this optimization is enabled, assignments where the lhs is an Identifier and the rhs is a private expression
        will update the cached value stored in the circuit instead of invalidating it.
        (since updated value == private expression result, the corresponding plaintext value is already
        available in the circuit)
        """
        return self._opt_cache_circuit_outputs

    @opt_cache_circuit_outputs.setter
    def opt_cache_circuit_outputs(self, val: bool):
        _type_check(val, bool)
        self._opt_cache_circuit_outputs = val

    @property
    def data_dir(self) -> str:
        """Path to directory where to store user data (e.g. generated encryption keys)."""
        return self._data_dir

    @data_dir.setter
    def data_dir(self, val: str):
        _type_check(val, str)
        import os
        if not os.path.exists(val):
            os.makedirs(val)
        self._data_dir = val

    @property
    def log_dir(self) -> str:
        """Path to default log directory."""
        return self._log_dir

    @log_dir.setter
    def log_dir(self, val: str):
        _type_check(val, str)
        import os
        if not os.path.exists(val):
            os.makedirs(val)
        self._log_dir = val

    @property
    def use_circuit_cache_during_testing_with_encryption(self) -> bool:
        """
        If true, snark keys for the test cases are cached
        (i.e. they are not regenerated on every run unless the circuit was modified)
        """
        return self._use_circuit_cache_during_testing_with_encryption

    @use_circuit_cache_during_testing_with_encryption.setter
    def use_circuit_cache_during_testing_with_encryption(self, val: bool):
        _type_check(val, bool)
        self._use_circuit_cache_during_testing_with_encryption = val

    @property
    def verbosity(self) -> int:
        """
        If 0, no output
        If 1, normal output
        If 2, verbose output

        This includes for example snark key- and proof generation output and
        information about intermediate transaction simulation steps.
        """
        return self._verbosity

    @verbosity.setter
    def verbosity(self, val: int):
        _type_check(val, int)
        self._verbosity = val
