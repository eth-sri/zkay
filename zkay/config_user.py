"""
This module defines the zkay options which are configurable by the user via command line arguments.

The argument parser in :py:mod:`.__main__` parses this file (as text) to gather help strings
and autocompletion information from the attribute docstrings.

WARNING: This is one of the only zkay modules that is imported before argcomplete.autocomplete is called. \
For performance reasons it should thus not have any import side-effects or perform any expensive operations during import.
"""
from typing import Any, Union, Set

import appdirs


class UserConfig:
    def __init__(self):
        # User configuration
        # Each attribute must have a type hint and a docstring for correct help strings in the commandline interface.
        # If 'Available Options: [...]' is specified, the options are used for autocomplete suggestions.

        self.proving_scheme: str = 'gm17'
        """
        NIZK proving scheme to use.

        Available Options: [gm17]
        """

        self.snark_backend: str = 'jsnark'
        """
        Snark backend to use.

        Available Options: [jsnark]
        """

        self.crypto_backend: str = 'dummy'
        """
        Encryption backend to use.

        Available Options: [dummy, rsa-pkcs1.5, rsa-oaep, ecdh-aes, ecdh-chaskey]
        """

        self.blockchain_backend: str = 'w3-eth-tester'
        """
        Backend to use when interacting with the blockchain.

        Running unit tests is only supported with w3-eth-tester and w3-ganache at the moment (because they need pre-funded dummy accounts).
        See https://web3py.readthedocs.io/en/stable/providers.html for more information

        Available Options: [w3-eth-tester, w3-ganache, w3-ipc, w3-websocket, w3-http, w3-custom]
        """

        self.blockchain_node_uri: Union[Any, str, None] = 'http://localhost:7545'
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

        self.indentation: str = ' '*4
        """Specifies the identation which should be used for the generated code output."""

        self.libsnark_check_verify_locally_during_proof_generation: bool = False
        """If true, the libsnark interface verifies locally whether the proof can be verified during proof generation."""

        self.opt_solc_optimizer_runs: int = 50
        """SOLC: optimize for how many times to run the code"""

        self.opt_hash_threshold: int = 70
        """
        If there are more than this many public circuit inputs (in uints), the hashing optimization will be used
        (only the hash of all public inputs will be passed as public input, public inputs are passed as private circuit inputs and
        the circuit verifies that the hash matches to ensure correctness)

        When hashing is enabled -> cheaper on-chain costs for verification (O(1) in #public args instead of O(n)),
        but much higher off-chain costs (key and proof generation time, memory consumption).
        """

        self.opt_eval_constexpr_in_circuit: bool = True
        """
        If true, literal expressions are folded and the result is baked into the circuit as a constant
        (as opposed to being evaluated outside the circuit and the result being moved in as an additional circuit input)
        """

        self.opt_cache_circuit_inputs: bool = True
        """
        If true, identifier circuit inputs will be cached (i.e. if an identifier is referenced multiple times within a private expression,
        or multiple times in different private expressions without being publicly written to in between,
        then the identifier will only be added to the circuit inputs once and all private uses will share the same input variable.
        """

        self.opt_cache_circuit_outputs: bool = True
        """
        Normally, the value cached in the circuit for a particular identifier must be invalidated whenever the identifier is
        assigned to in public code.

        If this optimization is enabled, assignments where the lhs is an Identifier and the rhs is a private expression
        will update the cached value stored in the circuit instead of invalidating it. (since updated value == private expression result,
        the corresponding plaintext value is already available in the circuit)
        """

        self.config_dir: str = appdirs.user_config_dir('zkay', False, None, True)
        """Path to directory where to store configuration data."""

        self.data_dir: str = appdirs.user_data_dir('zkay', False, None, True)
        """Path to directory where to store user data (e.g. generated encryption keys)."""

        self.log_dir: str = appdirs.user_log_dir('zkay')
        """Path to default log directory."""

        self.use_circuit_cache_during_testing_with_encryption: bool = True
        """If true, snark keys for the test cases are cached (i.e. they are not regenerated on every run unless the circuit was modified)"""

        self.verbose: bool = False
        """
        If true, print additional output.

        This includes for example snark key- and proof generation output and
        information about intermediate transaction simulation steps.
        """
