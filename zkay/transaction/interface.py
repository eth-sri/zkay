"""
This module defines the Runtime API, an abstraction layer which is used by the generated PythonOffchainSimulator classes.

It provides high level functions for

* blockchain interaction (deployment, state variable retrieval, transaction issuing, ...),
* cryptographic operations (encryption, decryption, key generation) and key management (local keystore)
* NIZK-proof generation
"""

import os
from abc import ABCMeta, abstractmethod
from builtins import type
from typing import Tuple, List, Optional, Union, Any, Dict, Collection

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.compiler.privacy.proving_scheme.proving_scheme import ProvingScheme
from zkay.transaction.crypto.params import CryptoParams
from zkay.zkay_ast.process_ast import get_verification_contract_names
from zkay.zkay_frontend import compile_zkay_file
from zkay.config import cfg, zk_print, zk_print_banner
from zkay.transaction.types import AddressValue, MsgStruct, BlockStruct, TxStruct, PublicKeyValue, Value, \
    PrivateKeyValue, CipherValue, RandomnessValue, KeyPair
from zkay.utils.progress_printer import success_print
from zkay.utils.timer import time_measure


class IntegrityError(Exception):
    """Exception which is raised when any part of a deployed zkay contract does not match the local contract file."""
    pass


class BlockChainError(Exception):
    """
    Exception which is raised when a blockchain interaction fails for any reason.
    """
    pass


class TransactionFailedException(BlockChainError):
    """Exception which is raised when a transaction fails."""
    pass


class ProofGenerationError(Exception):
    """Exception which is raised when proof generation fails."""
    pass


class ZkayBlockchainInterface(metaclass=ABCMeta):
    """
    API to interact with the blockchain.

    It automatically ensures that all needed library contracts are accessible.
    For most backends (except eth-tester), the necessary library contracts must be deployed in advance and \
    cfg.blockchain_pki_address or cfg.blockchain_crypto_lib_address must be specified.

    For safety reasons, zkay always verifies the integrity of remote contracts by comparing the evm bytecode \
    from the blockchain with the output obtained via local compilation of the corresponding source files.

    (Zkay ensures reproducibility via hard-coded solc versions/settings for global library contracts and by \
    using the version/settings stored in the manifest file for the main and verification contracts)

    See documentation of :py:meth:`connect` for more information.
    """

    def __init__(self):
        self._pki_contract = None
        self._lib_addresses = None

    def pki_contract(self, crypto_backend: str):
        if self._pki_contract is None:
            self._connect_libraries()
        return self._pki_contract[crypto_backend]

    @property
    def lib_addresses(self) -> Dict:
        if self._lib_addresses is None:
            self._connect_libraries()
        return self._lib_addresses

    @abstractmethod
    def _connect_libraries(self):
        pass

    # PUBLIC API

    @property
    def default_address(self) -> Optional[AddressValue]:
        """Return wallet address to use as from address when no address is explicitly specified."""
        addr = self._default_address()
        return None if addr is None else AddressValue(addr)

    def create_test_accounts(self, count: int) -> Tuple:
        """
        Return addresses of pre-funded accounts (only implemented for w3-eth-tester and w3-ganache, for debugging).

        :param count: how many accounts
        :raise NotImplementedError: if the backend does not support dummy accounts
        :raise ValueError: if not enough unused pre-funded accounts are available
        :return: the account addresses (either a single value if count = 1 or a tuple otherwise)
        """
        # may not be supported by all backends
        raise NotImplementedError('Current blockchain backend does not support creating pre-funded test accounts.')

    @abstractmethod
    def get_special_variables(self, sender: AddressValue, wei_amount: int = 0) -> Tuple[MsgStruct, BlockStruct, TxStruct]:
        """
        Return message, block and transaction objects, populated according to the current chain state.

        :param sender: transaction sender address
        :param wei_amount: transaction value (if payable)
        :return: populated builtin objects
        """
        pass

    def get_balance(self, address: AddressValue) -> int:
        """Return the balance of the wallet with the designated address (in wei)."""
        return self._get_balance(address.val)

    def req_public_key(self, address: AddressValue, crypto_params: CryptoParams) -> PublicKeyValue:
        """
        Request the public key for the designated address from the PKI contract.

        :param address: Address for which to request public key
        :raise BlockChainError: if request fails
        :return: the public key
        """
        assert isinstance(address, AddressValue)
        zk_print(f'Requesting public key for address "{address}"', verbosity_level=2)
        return self._req_public_key(address.val, crypto_params)

    def announce_public_key(self, sender: AddressValue, pk: PublicKeyValue, crypto_params: CryptoParams) -> Any:
        """
        Announce a public key to the PKI

        **WARNING: THIS ISSUES A CRYPTO CURRENCY TRANSACTION (GAS COST)**

        :param sender: public key owner, its eth private key must be hosted in the eth node to which the backend connects.
        :param pk: the public key to announce
        :raise BlockChainError: if there is an error in the backend
        :raise TransactionFailedException: if the announcement transaction failed
        :return: backend-specific transaction receipt
        """
        assert isinstance(sender, AddressValue)
        assert isinstance(pk, PublicKeyValue)
        zk_print(f'Announcing public key "{pk}" for address "{sender}"')
        return self._announce_public_key(sender.val, pk[:], crypto_params)

    def req_state_var(self, contract_handle, name: str, *indices) -> Union[bool, int, str, bytes]:
        """
        Request the contract state variable value name[indices[0]][indices[1]][...] from the chain.

        :param contract_handle: contract from which to read state
        :param name: name of the state variable
        :param indices: if the request is for an (nested) array/map index value, the values of all index keys.
        :raise BlockChainError: if request fails
        :return: The value
        """
        assert contract_handle is not None
        zk_print(f'Requesting state variable "{name}"', verbosity_level=2)
        val = self._req_state_var(contract_handle, name, *Value.unwrap_values(list(indices)))
        zk_print(f'Got value {val} for state variable "{name}"', verbosity_level=2)
        return val

    def call(self, contract_handle, sender: AddressValue, name: str, *args) -> Union[bool, int, str, bytes, List]:
        """
        Call the specified pure/view function in the given contract with the provided arguments.

        :param contract_handle: the contract in which the function resides
        :param sender: sender address, its eth private key must be hosted in the eth node to which the backend connects.
        :param name: name of the function to call
        :param args: argument values
        :raise BlockChainError: if request fails
        :return: function return value (single value if one return value, list if multiple return values)
        """
        assert contract_handle is not None
        zk_print(f'Calling contract function {name}{Value.collection_to_string(args)}', verbosity_level=2)
        val = self._call(contract_handle, sender.val, name, *Value.unwrap_values(list(args)))
        zk_print(f'Got return value {val}', verbosity_level=2)
        return val

    def transact(self, contract_handle, sender: AddressValue, function: str, actual_args: List, should_encrypt: List[bool], wei_amount: Optional[int] = None) -> Any:
        """
        Issue a transaction for the specified function in the given contract with the provided arguments

        **WARNING: THIS ISSUES A CRYPTO CURRENCY TRANSACTION (GAS COST)**

        :param contract_handle: the contract in which the function resides
        :param sender: sender address, its eth private key must be hosted in the eth node to which the backend connects.
        :param function: name of the function
        :param actual_args: the function argument values
        :param should_encrypt: a list which contains a boolean value for each argument, which should be true if the corresponding
                               parameter expects an encrypted/private value (this is only used for a last sanity-check)
        :param wei_amount: how much money to send along with the transaction (only for payable functions)
        :raise BlockChainError: if there is an error in the backend
        :raise TransactionFailedException: if the transaction failed
        :return: backend-specific transaction receipt
        """
        assert contract_handle is not None
        self.__check_args(actual_args, should_encrypt)
        zk_print(f'Issuing transaction for function "{function}" from account "{sender}"')
        zk_print(Value.collection_to_string(actual_args), verbosity_level=2)
        ret = self._transact(contract_handle, sender.val, function, *Value.unwrap_values(actual_args), wei_amount=wei_amount)
        zk_print()
        return ret

    def deploy(self, project_dir: str, sender: AddressValue, contract: str, actual_args: List, should_encrypt: List[bool], wei_amount: Optional[int] = None) -> Any:
        """
        Issue a deployment transaction which constructs the specified contract with the provided constructor arguments on the chain.

        **WARNING: THIS ISSUES A CRYPTO CURRENCY TRANSACTION (GAS COST)**

        :param project_dir: directory where the zkay file, manifest and snark keys reside
        :param sender: creator address, its eth private key must be hosted in the eth node to which the backend connects.
        :param contract: name of the contract to instantiate
        :param actual_args: the constructor argument values
        :param should_encrypt: a list which contains a boolean value for each argument, which should be true if the corresponding
                               parameter expects an encrypted/private value (this is only used for a last sanity-check)
        :param wei_amount: how much money to send along with the constructor transaction (only for payable constructors)
        :raise BlockChainError: if there is an error in the backend
        :raise TransactionFailedException: if the deployment transaction failed
        :return: handle for the newly created contract
        """
        if not self.is_debug_backend() and cfg.crypto_backend == 'dummy':
            raise BlockChainError('SECURITY ERROR: Dummy encryption can only be used with debug blockchain backends (w3-eth-tester or w3-ganache).')

        zk_print_banner(f'Deploy {contract}')

        self.__check_args(actual_args, should_encrypt)
        zk_print(f'Deploying contract {contract}{Value.collection_to_string(actual_args)}')
        ret = self._deploy(project_dir, sender.val, contract, *Value.unwrap_values(actual_args), wei_amount=wei_amount)
        zk_print()
        return ret

    def connect(self, project_dir: str, contract: str, contract_address: AddressValue, user_address: AddressValue) -> Any:
        """
        Create a handle which can be used to interact with an existing contract on the chain after verifying its integrity.

        Project dir must contain a .zkay file, a manifest.json file as well as a \
        subdirectory *verification_contract_name*\\ _out containing 'proving.key' and 'verification.key' for each verification contract.
        These files are referred to as 'local' files in the following explanation.

        If this function succeeds, it is guaranteed, that:

        * the remote main contract at contract_address, matches the solidity contract obtained by running zkay on the local zkay file
          using the configuration stored in the local manifest
        * the pki contract referenced in the remote main contract matches the correct zkay pki contract
        * the verification contracts referenced in the remote solidity contract were generated by running zkay on a zkay file
          equivalent to local zkay file, with zk-snark keys which match the local keys.
        * the library contract referenced in the verification contracts matches the correct zkay library contract

        This reduces the required trust to the zk-snark setup phase (i.e. you must trust that prover/verification keys
        were generated for the correct circuit), since you can inspect the source code of the local zkay file and check it
        for malicious behavior yourself (and the zkay implementation, which performs the transformation, is open source as well).

        Example Scenarios:

        a) the remote zkay contract is benign (generated by and deployed using zkay):
           -> you will only be able to connect if the local files are equivalent -> correctness is guaranteed
        b) the remote zkay contract was tampered with (any of the .sol files was modified was modified before deployment)
           -> connection will fail, because local zkay compilation will not produce matching evm bytecode
        c) the prover/verification keys were tampered with (they were generated for a different circuit than the one produced by zkay)

           * local keys are genuine -> connection will be refused because the keys don't match what is baked into the remote verification contract
           * same tampered keys locally -> NO GUARANTEES, since the trust assumption is violated

        :param project_dir: directory where the zkay file, manifest and snark keys reside
        :param contract: name of the contract to connect to
        :param contract_address: address of the deployed contract
        :param user_address: account which connects to the contract
        :raise IntegrityError: if the integrity check fails (mismatch between local code and remote contract)
        :return: contract handle for the specified contract
        """
        if not self.is_debug_backend() and cfg.crypto_backend == 'dummy':
            raise BlockChainError('SECURITY ERROR: Dummy encryption can only be used with debug blockchain backends (w3-eth-tester or w3-ganache).')

        zk_print_banner(f'Connect to {contract}@{contract_address}')

        # If not already done, compile zkay file to generate main and verification contracts (but don't generate new prover/verification keys and manifest)
        zk_file = os.path.join(project_dir, 'contract.zkay')
        if not os.path.exists(zk_file):
            raise IntegrityError('No zkay contract found in specified directory')
        verifier_names = []
        if not os.path.exists(os.path.join(project_dir, 'contract.sol')):
            compile_zkay_file(zk_file, project_dir, import_keys=True, verifier_names=verifier_names)
        else:
            with open(zk_file) as f:
                verifier_names = get_verification_contract_names(f.read())

        zk_print(f'Connecting to contract {contract}@{contract_address}')
        contract_on_chain = self._connect(project_dir, contract, contract_address.val)

        pki_verifier_addresses = {}

        # Check integrity of all pki contracts
        self._pki_contract = {}
        for crypto_params in cfg.all_crypto_params():  # TODO: Only for used homomorphisms?
            contract_name = cfg.get_pki_contract_name(crypto_params)
            pki_address = self._req_state_var(contract_on_chain, f'{contract_name}_inst')
            pki_verifier_addresses[contract_name] = AddressValue(pki_address)
            with cfg.library_compilation_environment():
                contract = self._verify_contract_integrity(pki_address, os.path.join(project_dir, f'{contract_name}.sol'))
                self._pki_contract[crypto_params.crypto_name] = contract

        # Check verifier contract and library integrity
        if verifier_names:
            some_vname = verifier_names[0]

            libraries = [(lib_name, os.path.join(project_dir, ProvingScheme.verify_libs_contract_filename)) for lib_name in cfg.external_crypto_lib_names]
            some_vcontract = self._req_state_var(contract_on_chain, f'{some_vname}_inst')
            libs = self._verify_library_integrity(libraries, some_vcontract, os.path.join(project_dir, f'{some_vname}.sol'))
            self._lib_addresses = libs

            for verifier in verifier_names:
                v_address = self._req_state_var(contract_on_chain, f'{verifier}_inst')
                pki_verifier_addresses[verifier] = AddressValue(v_address)
                vcontract = self._verify_contract_integrity(v_address, os.path.join(project_dir, f'{verifier}.sol'), libraries=libs)

                # Verify prover key
                expected_hash = self._req_state_var(vcontract, cfg.prover_key_hash_name)
                from zkay.transaction.runtime import Runtime
                actual_hash = Runtime.prover().get_prover_key_hash(os.path.join(project_dir, cfg.get_circuit_output_dir_name(verifier)))
                if expected_hash != actual_hash:
                    raise IntegrityError(f'Prover key hash in deployed verification contract does not match local prover key file for "{verifier}"')

        # Check zkay contract integrity
        self._verify_zkay_contract_integrity(contract_on_chain.address, project_dir, pki_verifier_addresses)

        with success_print():
            zk_print(f'OK: Bytecode on blockchain matches local zkay contract')
        zk_print(f'Connection from account 0x{user_address} established\n')

        return contract_on_chain

    @abstractmethod
    def deploy_solidity_contract(self, sol_filename: str, contract_name: Optional[str], sender: Union[bytes, str]) -> str:
        """
        Compile and deploy the specified solidity contract.

        :param sol_filename: solidity file
        :param contract_name: specifies which contract from the .sol file to compile (None -> take first contract in file)
        :param sender: account address from which to issue the deployment transaction (keys must be hosted in node)
        :raise BlockChainError: if there is an error in the backend
        :raise TransactionFailedException: if the deployment transaction failed
        :return: Address of the deployed contract
        """
        pass

    @classmethod
    def is_debug_backend(cls) -> bool:
        return False

    # INTERNAL FUNCTIONALITY

    @abstractmethod
    def _verify_contract_integrity(self, address: str, sol_filename: str, *,
                                   libraries: Dict = None, contract_name: str = None, is_library: bool = False) -> Any:
        """
        Check if the bytecode of the contract at address matches the bytecode obtained by locally compiling sol_filename.

        :param address: address of the remote contract
        :param sol_filename: path to the local contract code file
        :param libraries: library dict which should be passed during compilation (for linking)
        :param contract_name: contract name, if not specified, the first contract in the file is used
        :param is_library: set to true if this a library instead of a contract
        :raise IntegrityError: if there is a mismatch
        :return: a contract handle for the remote contract
        """
        pass

    @abstractmethod
    def _verify_library_integrity(self, libraries: List[Tuple[str, str]], contract_with_libs_addr: str, sol_with_libs_filename: str) -> Dict[str, str]:
        """
        Check if the libraries linked in contract_with_libs match library_sol and return the addresses of the library contracts.

        :param libraries: = List of (library name, library.sol) tuples
        :raise IntegrityError: if there is a mismatch
        :return: Dict of library name -> address for all libs from libraries which occurred in contract@contract_with_libs_addr
        """
        pass

    @abstractmethod
    def _verify_zkay_contract_integrity(self, address: str, project_dir: str, pki_verifier_addresses: dict):
        """
        Check if the zkay main contract at address matches the local file

        :param address: address of the remote main contract
        :param project_dir: path to the zkay contract directory
        :param pki_verifier_addresses: dictionary which maps pki and verification contract names to the corresponding remote addresses
        :raise IntegrityError: if there is a mismatch
        """
        pass

    @abstractmethod
    def _default_address(self) -> Union[None, bytes, str]:
        pass

    @abstractmethod
    def _get_balance(self, address: Union[bytes, str]) -> int:
        pass

    @abstractmethod
    def _deploy_dependencies(self, sender: Union[bytes, str], project_dir: str, verifier_names: List[str]) -> Dict[str, AddressValue]:
        pass

    @abstractmethod
    def _req_public_key(self, address: Union[bytes, str], crypto_params: CryptoParams) -> PublicKeyValue:
        pass

    @abstractmethod
    def _announce_public_key(self, address: Union[bytes, str], pk: Tuple[int, ...], crypto_params: CryptoParams) -> Any:
        pass

    @abstractmethod
    def _call(self, contract_handle, sender: Union[bytes, str], name: str, *args) -> Union[bool, int, str]:
        pass

    @abstractmethod
    def _req_state_var(self, contract_handle, name: str, *indices) -> Union[bool, int, str]:
        pass

    @abstractmethod
    def _transact(self, contract_handle, sender: Union[bytes, str], function: str, *actual_args, wei_amount: Optional[int] = None) -> Any:
        pass

    @abstractmethod
    def _deploy(self, project_dir: str, sender: Union[bytes, str], contract: str, *actual_args, wei_amount: Optional[int] = None) -> Any:
        pass

    @abstractmethod
    def _connect(self, project_dir: str, contract: str, address: Union[bytes, str]) -> Any:
        pass

    @staticmethod
    def __check_args(actual_args: List, should_encrypt: List[bool]):
        assert len(actual_args) == len(should_encrypt)
        for idx, arg in enumerate(actual_args):
            assert not isinstance(arg, PrivateKeyValue) and not isinstance(arg, RandomnessValue)
            assert should_encrypt[idx] == isinstance(arg, CipherValue)


class ZkayKeystoreInterface(metaclass=ABCMeta):
    """API to add and retrieve local key pairs, and to request public keys."""

    def __init__(self, conn: ZkayBlockchainInterface, crypto_params: CryptoParams):
        self.conn = conn
        self.crypto_params = crypto_params
        self.local_pk_store: Dict[AddressValue, PublicKeyValue] = {}
        self.local_key_pairs: Dict[AddressValue, KeyPair] = {}

    def add_keypair(self, address: AddressValue, key_pair: KeyPair):
        """
        Import cryptographic keys for address into this keystore and announce the public key to the pki if necessary.

        :param address: Address to which the keys belong
        :param key_pair: cryptographic keys
        :raise TransactionFailedException: if announcement transaction fails
        """
        self.local_key_pairs[address] = key_pair
        # Announce if not yet in pki
        try:
            self.conn.req_public_key(address, self.crypto_params)
        except BlockChainError:
            self.conn.announce_public_key(address, key_pair.pk, self.crypto_params)

    def has_initialized_keys_for(self, address: AddressValue) -> bool:
        """Return true if keys for address are already in the store."""
        return address in self.local_key_pairs

    def getPk(self, address: AddressValue) -> PublicKeyValue:
        """
        Return public key for address.

        If the key is cached locally, returned the cached copy, otherwise request from pki contract.

        NOTE: At the moment, the name of this function must match the name in the pki contract.

        :param address: address to which the public key belongs
        :raise BlockChainError: if key request fails
        :return: the public key
        """
        assert isinstance(address, AddressValue)
        zk_print(f'Requesting public key for address {address.val}', verbosity_level=2)
        if address in self.local_pk_store:
            return self.local_pk_store[address]
        else:
            pk = self.conn.req_public_key(address, self.crypto_params)
            self.local_pk_store[address] = pk
            return pk

    def sk(self, address: AddressValue) -> PrivateKeyValue:
        """
        Return secret key for address from the local key store.

        Only works for keys which were previously added through add_keypair

        :param address: address to which the private key belongs
        :raise KeyError: if key not in local store
        :return: private key
        """
        return self.local_key_pairs[address].sk

    def pk(self, address: AddressValue) -> PublicKeyValue:
        """
        Return public key for address from the local key store.

        Only works for keys which were previously added through add_keypair

        :param address: address to which the public key belongs
        :raise KeyError: if key not in local store
        :return: public key
        """
        return self.local_key_pairs[address].pk


class ZkayCryptoInterface(metaclass=ABCMeta):
    """API to generate cryptographic keys and perform encryption/decryption operations."""

    def __init__(self, keystore: ZkayKeystoreInterface):
        self.keystore = keystore

    @property
    @abstractmethod
    def params(self) -> CryptoParams:
        pass

    def generate_or_load_key_pair(self, address: AddressValue):
        """
        Store cryptographic keys for the account with the specified address in the keystore.

        If the pre-existing keys are found for this address, they are loaded from the filesystem, \
        otherwise new keys are generated.

        :param address: the address for which to generate keys
        """
        self.keystore.add_keypair(address, self._generate_or_load_key_pair(address.val.hex()))

    def enc(self, plain: Union[int, AddressValue], my_addr: AddressValue, target_addr: AddressValue) -> Tuple[CipherValue, Optional[RandomnessValue]]:
        """
        Encrypt plain for receiver with target_addr.

        :param plain: plain text to encrypt
        :param my_addr: address of the sender who encrypts
        :param target_addr: address of the receiver for whom to encrypt
        :return: if symmetric -> (iv_cipher, None), if asymmetric (cipher, randomness which was used to encrypt plain)
        """
        if isinstance(plain, AddressValue):
            plain = int.from_bytes(plain.val, byteorder='big')
        assert not isinstance(plain, Value), f"Tried to encrypt value of type {type(plain).__name__}"
        assert isinstance(my_addr, AddressValue) and isinstance(target_addr, AddressValue)
        assert int(plain) < bn128_scalar_field, f"Integer overflow, plaintext is >= field prime"
        zk_print(f'Encrypting value {plain} for destination "{target_addr}"', verbosity_level=2)

        sk = self.keystore.sk(my_addr).val
        raw_pk = self.keystore.getPk(target_addr)
        if self.params.is_symmetric_cipher():
            assert len(raw_pk) == 1
            pk = raw_pk[0]
        else:
            pk = self.deserialize_pk(raw_pk[:])
        while True:
            # Retry until cipher text is not 0
            cipher, rnd = self._enc(int(plain), sk, pk)
            cipher = CipherValue(cipher, params=self.params)
            rnd = RandomnessValue(rnd, params=self.params) if rnd is not None else None
            if cipher != CipherValue(params=self.params):
                break

        return cipher, rnd

    def dec(self, cipher: CipherValue, my_addr: AddressValue) -> Tuple[int, Optional[RandomnessValue]]:
        """
        Decrypt cipher encrypted for my_addr.

        :param cipher: encrypted value
        :param my_addr: cipher is encrypted for this address
        :return: if symmetric -> (plain, None), if asymmetric (plain, randomness which was used to encrypt plain)
        """
        assert isinstance(cipher, CipherValue), f"Tried to decrypt value of type {type(cipher).__name__}"
        assert isinstance(my_addr, AddressValue)
        zk_print(f'Decrypting value {cipher} for {my_addr}', verbosity_level=2)

        if cipher == CipherValue(params=self.params):
            # Ciphertext is all zeros, i.e. uninitialized -> zero
            return 0, (None if self.params.is_symmetric_cipher() else RandomnessValue(params=self.params))
        else:
            sk = self.keystore.sk(my_addr)
            plain, rnd = self._dec(cipher[:], sk.val)
            return plain, (None if rnd is None else RandomnessValue(rnd, params=self.params))

    def serialize_pk(self, key: int, total_bytes: int) -> List[int]:
        """Serialize a large integer into an array of {params.cipher_chunk_size}-byte ints."""
        data = key.to_bytes(total_bytes, byteorder='big')
        return ZkayCryptoInterface.pack_byte_array(data, self.params.cipher_chunk_size)

    def deserialize_pk(self, arr: Collection[int]) -> int:
        """Deserialize an array of {params.cipher_chunk_size}-byte ints into a single large int"""
        data = ZkayCryptoInterface.unpack_to_byte_array(arr, self.params.cipher_chunk_size, 0)
        return int.from_bytes(data, byteorder='big')

    @staticmethod
    def pack_byte_array(bin: bytes, chunk_size) -> List[int]:
        """Pack byte array into an array of {chunk_size}-byte ints"""
        total_bytes = len(bin)
        first_chunk_size = total_bytes % chunk_size
        arr = [] if first_chunk_size == 0 else [int.from_bytes(bin[:first_chunk_size], byteorder='big')]
        for i in range(first_chunk_size, total_bytes - first_chunk_size, chunk_size):
            arr.append(int.from_bytes(bin[i:i + chunk_size], byteorder='big'))
        return list(reversed(arr))

    @staticmethod
    def unpack_to_byte_array(arr: Collection[int], chunk_size: int, desired_length: int) -> bytes:
        """Unpack an array of {chunk_size}-byte ints into a byte array"""
        return b''.join(chunk.to_bytes(chunk_size, byteorder='big') for chunk in reversed(list(arr)))[-desired_length:]

    # Interface implementation

    @abstractmethod
    def _generate_or_load_key_pair(self, address: str) -> KeyPair:
        pass

    @abstractmethod
    def _enc(self, plain: int, my_sk: int, target_pk: int) -> Tuple[List[int], List[int]]:
        pass

    @abstractmethod
    def _dec(self, cipher: Tuple[int, ...], sk: Any) -> Tuple[int, List[int]]:
        pass


class ZkayProverInterface(metaclass=ABCMeta):
    """API to generate zero knowledge proofs for a particular circuit and arguments."""

    def __init__(self, proving_scheme: str = None):
        self.proving_scheme = cfg.proving_scheme if proving_scheme is None else proving_scheme

    def generate_proof(self, project_dir: str, contract: str, function: str, priv_values: List, in_vals: List, out_vals: List[Union[int, CipherValue]]) -> List[int]:
        """
        Generate a NIZK-proof using the provided circuit for the given arguments.

        Note: circuit arguments must be in the same order as they are declared inside the circuit. (i.e. in execution order)

        :param project_dir: directory where the manifest and the prover keys are located
        :param contract: contract of which the function which requires verification is part of
        :param function: the contract member function for which a proof needs to be generated
        :param priv_values: private/auxiliary circuit inputs in correct order
        :param in_vals: public circuit inputs in correct order
        :param out_vals: public circuit outputs in correct order
        :raise ProofGenerationError: if proof generation fails
        :return: the proof, serialized into an uint256 array
        """
        for i in range(len(priv_values)):
            arg = priv_values[i]
            assert not isinstance(arg, Value) or isinstance(arg, (RandomnessValue, AddressValue))
            if isinstance(arg, AddressValue):
                priv_values[i] = int.from_bytes(arg.val, byteorder='big')

        zk_print(f'Generating proof for {contract}.{function}')
        zk_print(f'[priv: {Value.collection_to_string(priv_values)}] '
                 f'[in: {Value.collection_to_string(in_vals)}] [out: {Value.collection_to_string(out_vals)}]', verbosity_level=2)

        priv_values, in_vals, out_vals = Value.unwrap_values(Value.flatten(priv_values)), Value.unwrap_values(in_vals), Value.unwrap_values(out_vals)

        # Check for overflows
        for arg in priv_values + in_vals + out_vals:
            assert int(arg) < bn128_scalar_field, 'argument overflow'

        with time_measure(f'generate_proof', True):
            verify_dir = cfg.get_circuit_output_dir_name(cfg.get_verification_contract_name(contract, function))
            return self._generate_proof(os.path.join(project_dir, verify_dir), priv_values, in_vals, out_vals)

    @abstractmethod
    def _generate_proof(self, verifier_dir: str, priv_values: List[int], in_vals: List[int], out_vals: List[int]) -> List[int]:
        pass

    @abstractmethod
    def get_prover_key_hash(self, verifier_directory: str) -> bytes:
        """Return the hash of the prover key stored in the given verification contract output directory."""
        pass
