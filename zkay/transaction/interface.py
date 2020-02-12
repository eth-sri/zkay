import json
import os
from abc import ABCMeta, abstractmethod
from builtins import type
from typing import Tuple, List, Optional, Union, Any, Dict, Collection

from zkay.compiler.privacy.zkay_frontend import compile_zkay_file
from zkay.config import cfg, debug_print

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.compiler.privacy.manifest import Manifest
from zkay.transaction.types import AddressValue, MsgStruct, BlockStruct, TxStruct, PublicKeyValue, Value, PrivateKeyValue, CipherValue, \
    RandomnessValue, KeyPair
from zkay.utils.progress_printer import colored_print, TermColor
from zkay.utils.timer import time_measure


def parse_manifest(project_dir: str):
    with open(os.path.join(project_dir, 'manifest.json')) as f:
        j = json.loads(f.read())
        j[Manifest.project_dir] = project_dir
    return j


class ZkayBlockchainInterface(metaclass=ABCMeta):
    @property
    def default_address(self) -> AddressValue:
        return self._default_address()

    def deploy_libraries(self, sender: AddressValue):
        self._deploy_libraries(sender.val)

    def create_test_accounts(self, count: int) -> Tuple:
        # may not be supported by all backends
        raise NotImplementedError('Current blockchain backend does not support creating pre-funded test accounts.')

    @abstractmethod
    def get_special_variables(self, sender: AddressValue, value: int = 0) -> Tuple[MsgStruct, BlockStruct, TxStruct]:
        pass

    def get_balance(self, address: AddressValue) -> int:
        return self._get_balance(address.val)

    def req_public_key(self, address: AddressValue) -> PublicKeyValue:
        assert isinstance(address, AddressValue)
        debug_print(f'Requesting public key for address "{address}"')
        return self._req_public_key(address.val)

    def announce_public_key(self, address: AddressValue, pk: PublicKeyValue):
        assert isinstance(address, AddressValue)
        assert isinstance(pk, PublicKeyValue)
        debug_print(f'Announcing public key "{pk}" for address "{address}"')
        self._announce_public_key(address.val, pk[:])

    def req_state_var(self, contract_handle, name: str, *indices) -> Union[bool, int, str]:
        assert contract_handle is not None
        debug_print(f'Requesting state variable "{name}"')
        val = self._req_state_var(contract_handle, name, *Value.unwrap_values(list(indices)))
        debug_print(f'Got value {val} for state variable "{name}"')
        return val

    def call(self, contract_handle, name: str, *args) -> Union[bool, int, str, List]:
        assert contract_handle is not None
        debug_print(f'Calling contract function {name}{Value.collection_to_string(args)}')
        val = self._req_state_var(contract_handle, name, *Value.unwrap_values(list(args)))
        debug_print(f'Got return value {val}')
        return val

    def transact(self, contract_handle, sender: AddressValue, function: str, actual_args: List, should_encrypt: List[bool], value: Optional[int] = None) -> Any:
        assert contract_handle is not None
        self.__check_args(actual_args, should_encrypt)
        debug_print(f'Issuing transaction for function "{function}"{Value.collection_to_string(actual_args)})')
        return self._transact(contract_handle, sender.val, function, *Value.unwrap_values(actual_args), value=value)

    def deploy(self, project_dir: str, sender: AddressValue, contract: str, actual_args: List, should_encrypt: List[bool], value: Optional[int] = None) -> Any:
        self.__check_args(actual_args, should_encrypt)
        debug_print(f'Deploying contract {contract}{Value.collection_to_string(actual_args)}')
        return self._deploy(parse_manifest(project_dir), sender.val, contract, *Value.unwrap_values(actual_args), value=value)

    def connect(self, project_dir: str, contract: str, contract_address: AddressValue) -> Any:
        manifest = parse_manifest(project_dir)

        # Compile zkay file, generate circuits and verification contracts (but don't generate new prover/verification keys and manifest)
        compile_zkay_file(os.path.join(project_dir, manifest[Manifest.zkay_contract_filename]), project_dir, import_keys=True)

        debug_print(f'Connecting to contract {contract}@{contract_address}')
        contract_on_chain = self._connect(manifest, contract, contract_address.val)

        pki_verifier_addresses = {}

        # Check pki integrity
        pki_address = self._req_state_var(contract_on_chain, f'{cfg.pki_contract_name}_inst')
        pki_verifier_addresses[cfg.pki_contract_name] = AddressValue(pki_address)
        self._verify_contract_integrity(pki_address, os.path.join(project_dir, manifest[Manifest.pki_lib]))

        # Check verifier contract and library integrity
        verifier_names = manifest[Manifest.verifier_names].values()
        if verifier_names:
            some_vname = next(iter(verifier_names))
            libraries = [('BN256G2', os.path.join(project_dir, manifest[Manifest.verify_lib]))]
            some_vcontract = self._req_state_var(contract_on_chain, f'{some_vname}_inst')
            libs = self._verify_library_integrity(libraries, some_vcontract, os.path.join(project_dir, f'{some_vname}.sol'))

            for verifier in verifier_names:
                v_address = self._req_state_var(contract_on_chain, f'{verifier}_inst')
                pki_verifier_addresses[verifier] = AddressValue(v_address)
                self._verify_contract_integrity(v_address, os.path.join(project_dir, f'{verifier}.sol'), libraries=libs)

        # Check zkay contract integrity
        self._verify_zkay_contract_integrity(contract_on_chain.address, os.path.join(project_dir, manifest[Manifest.contract_filename]), pki_verifier_addresses)

        with colored_print(TermColor.OKGREEN):
            debug_print(f'OK: Bytecode on blockchain matches local zkay contract')

        return contract_on_chain

    @abstractmethod
    def _verify_contract_integrity(self, address: str, sol_filename: str, *,
                                   libraries: Dict = None, contract_name: str = None, is_library: bool = False):
        pass

    @abstractmethod
    def _verify_library_integrity(self, libraries: List[Tuple[str, str]], contract_with_libs_addr: str, sol_with_libs_filename: str) -> Dict[str, str]:
        """
        Checks if the libraries linked in contract_with_libs match library_sol and returns the addresses of the library contracts
        :param libraries: = List of (library name, library.sol) tuples
        :return Dict of library name -> address for all libs from libraries which occurred in contract@contract_with_libs_addr
        """
        pass

    def _verify_zkay_contract_integrity(self, address: str, sol_file: str, pki_verifier_addresses):
        pass

    @abstractmethod
    def _default_address(self) -> AddressValue:
        pass

    @abstractmethod
    def _get_balance(self, address: Union[bytes, str]) -> int:
        pass

    @abstractmethod
    def _pki_verifier_addresses(self, sender: str, manifest) -> Dict[str, AddressValue]:
        pass

    @abstractmethod
    def _req_public_key(self, address: Union[bytes, str]) -> PublicKeyValue:
        pass

    @abstractmethod
    def _announce_public_key(self, address: Union[bytes, str], pk: Tuple[int, ...]) -> PublicKeyValue:
        pass

    @abstractmethod
    def _req_state_var(self, contract_handle, name: str, *indices) -> Union[bool, int, str]:
        pass

    @abstractmethod
    def _transact(self, contract_handle, sender: Union[bytes, str], function: str, *actual_args, value: Optional[int] = None) -> Any:
        pass

    @abstractmethod
    def _deploy(self, manifest, sender: Union[bytes, str], contract: str, *actual_args, value: Optional[int] = None) -> Any:
        pass

    @abstractmethod
    def _deploy_libraries(self, sender: Union[bytes, str]):
        pass

    @abstractmethod
    def _connect(self, manifest, contract: str, address: Union[bytes, str]) -> Any:
        pass

    @staticmethod
    def __check_args(actual_args: List, should_encrypt: List[bool]):
        assert len(actual_args) == len(should_encrypt)
        for idx, arg in enumerate(actual_args):
            assert not isinstance(arg, PrivateKeyValue) and not isinstance(arg, RandomnessValue)
            assert should_encrypt[idx] == isinstance(arg, CipherValue)


class ZkayCryptoInterface(metaclass=ABCMeta):
    def generate_or_load_key_pair(self, address: AddressValue) -> KeyPair:
        return self._generate_or_load_key_pair(address.val.hex())

    def enc(self, plain: Union[int, AddressValue], pk: PublicKeyValue) -> Tuple[CipherValue, RandomnessValue]:
        """
        Encrypts plain with the provided public key
        :param plain: plain text to encrypt
        :param pk: public key
        :return: Tuple(cipher text, randomness which was used to encrypt plain)
        """
        if isinstance(plain, AddressValue):
            plain = int.from_bytes(plain.val, byteorder='big')
        assert not isinstance(plain, Value), f"Tried to encrypt value of type {type(plain).__name__}"
        assert isinstance(pk, PublicKeyValue), f"Tried to use public key of type {type(pk).__name__}"
        assert int(plain) < bn128_scalar_field, f"Integer overflow, plaintext is > field prime"
        debug_print(f'Encrypting value {plain} with public key "{pk}"')

        while True:
            # Retry until cipher text is not 0
            cipher, rnd = self._enc(int(plain), self.deserialize_bigint(pk[:]))
            cipher, rnd = CipherValue(cipher), RandomnessValue(rnd)
            if cipher != CipherValue():
                break
        return cipher, rnd

    def dec(self, cipher: CipherValue, sk: PrivateKeyValue) -> Tuple[int, RandomnessValue]:
        """
        Decrypts cipher with the provided secret key
        :param cipher: encrypted value
        :param sk: secret key
        :return: Tuple(plain text, randomness which was used to encrypt plain)
        """
        assert isinstance(cipher, CipherValue), f"Tried to decrypt value of type {type(cipher).__name__}"
        assert isinstance(sk, PrivateKeyValue), f"Tried to use private key of type {type(sk).__name__}"
        debug_print(f'Decrypting value {cipher} with secret key "{sk}"')
        if len(cipher) == 1 and isinstance(cipher[0], AddressValue):
            cipher = CipherValue(cipher[0].val)
            was_address = True
        else:
            was_address = False

        if cipher == CipherValue():
            ret = 0, RandomnessValue()
        else:
            plain, rnd = self._dec(cipher[:], sk.val)
            ret = plain, RandomnessValue(rnd)

        if was_address:
            ret = AddressValue(ret[0]), ret[1]
        return ret

    @staticmethod
    def serialize_bigint(key: int, total_bytes: int) -> List[int]:
        bin = key.to_bytes(total_bytes, byteorder='big')
        return ZkayCryptoInterface.pack_byte_array(bin)

    @staticmethod
    def pack_byte_array(bin: bytes, chunk_size=cfg.pack_chunk_size) -> List[int]:
        total_bytes = len(bin)
        first_chunk_size = total_bytes % chunk_size
        arr = [] if first_chunk_size == 0 else [int.from_bytes(bin[:first_chunk_size], byteorder='big')]
        for i in range(first_chunk_size, total_bytes - first_chunk_size, chunk_size):
            arr.append(int.from_bytes(bin[i:i + chunk_size], byteorder='big'))
        return list(reversed(arr))

    @staticmethod
    def deserialize_bigint(arr: Collection[int]) -> int:
        bin = ZkayCryptoInterface.unpack_to_byte_array(arr, 0)
        return int.from_bytes(bin, byteorder='big')

    @staticmethod
    def unpack_to_byte_array(arr: Collection[int], desired_length: int) -> bytes:
        return b''.join(chunk.to_bytes(cfg.pack_chunk_size, byteorder='big') for chunk in reversed(list(arr)))[-desired_length:]

    @abstractmethod
    def _generate_or_load_key_pair(self, address: str) -> KeyPair:
        pass

    @abstractmethod
    def _enc(self, plain: int, pk: int) -> Tuple[List[int], List[int]]:
        pass

    @abstractmethod
    def _dec(self, cipher: Tuple[int, ...], sk: Any) -> Tuple[int, List[int]]:
        pass


class ZkayKeystoreInterface:
    def __init__(self, conn: ZkayBlockchainInterface):
        self.conn = conn
        self.local_pk_store: Dict[AddressValue, PublicKeyValue] = {}
        self.local_key_pairs: Dict[AddressValue, KeyPair] = {}

    def add_keypair(self, address: AddressValue, key_pair: KeyPair):
        self.local_key_pairs[address] = key_pair
        # Announce if not yet in pki
        try:
            self.conn.req_public_key(address)
        except:
            self.conn.announce_public_key(address, key_pair.pk)

    def getPk(self, address: AddressValue) -> PublicKeyValue:
        assert isinstance(address, AddressValue)
        debug_print(f'Requesting public key for address {address.val}')
        if address in self.local_pk_store:
            return self.local_pk_store[address]
        else:
            pk = self.conn.req_public_key(address)
            self.local_pk_store[address] = pk
            return pk

    def sk(self, address: AddressValue) -> PrivateKeyValue:
        return self.local_key_pairs[address].sk

    def pk(self, address: AddressValue) -> PublicKeyValue:
        return self.local_key_pairs[address].pk


class ZkayProverInterface(metaclass=ABCMeta):
    def __init__(self, proving_scheme: str = cfg.proving_scheme):
        self.proving_scheme = proving_scheme

    def generate_proof(self, project_dir: str, contract: str, function: str, priv_values: List, in_vals: List, out_vals: List[Union[int, CipherValue]]) -> List[int]:
        for i in range(len(priv_values)):
            arg = priv_values[i]
            assert not isinstance(arg, Value) or isinstance(arg, (RandomnessValue, AddressValue))
            if isinstance(arg, AddressValue):
                priv_values[i] = int.from_bytes(arg.val, byteorder='big')

        debug_print(f'Generating proof for {contract}.{function} [priv: {Value.collection_to_string(priv_values)}] '
                    f'[in: {Value.collection_to_string(in_vals)}] [out: {Value.collection_to_string(out_vals)}]')

        priv_values, in_vals, out_vals = Value.unwrap_values(Value.flatten(priv_values)), Value.unwrap_values(in_vals), Value.unwrap_values(out_vals)

        # Check for overflows
        for arg in priv_values + in_vals + out_vals:
            assert int(arg) < bn128_scalar_field, 'argument overflow'

        manifest = parse_manifest(project_dir)
        with time_measure(f'generate_proof_{contract}.{function}', True):
            return self._generate_proof(os.path.join(project_dir, f"{manifest[Manifest.verifier_names][f'{contract}.{function}']}_out"),
                                        priv_values, in_vals, out_vals)

    @abstractmethod
    def _generate_proof(self, verifier_dir: str, priv_values: List[int], in_vals: List[int], out_vals: List[int]) -> List[int]:
        pass
