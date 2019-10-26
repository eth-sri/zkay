import json
import os
from abc import ABCMeta, abstractmethod
from typing import Tuple, List, Optional, Union, Any, Dict

from zkay.compiler.privacy.manifest import Manifest

__debug_print = True
default_proving_scheme = 'gm17'
bn256_scalar_field = 21888242871839275222246405745257275088548364400416034343698204186575808495617


def debug_print(*args):
    if __debug_print:
        print(*args)


class Value:
    def __init__(self, val):
        self.val = val

    def __str__(self):
        return f'{type(self).__name__}({self.val})'

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.val == other.val

    def __hash__(self):
        return self.val.__hash__()

    @staticmethod
    def unwrap_values(v: Optional[Union[int, bool, 'Value', List]]) -> Union[int, List]:
        if v is None:
            return []

        if isinstance(v, List):
            return list(map(Value.unwrap_values, v))
        else:
            return v.val if isinstance(v, Value) else v


class CipherValue(Value):
    pass


class PrivateKeyValue(Value):
    pass


class PublicKeyValue(Value):
    pass


class RandomnessValue(Value):
    pass


class AddressValue(Value):
    def __init__(self, val: str):
        super().__init__(val)


class KeyPair:
    def __init__(self, pk: PublicKeyValue, sk: PrivateKeyValue):
        self.pk = pk
        self.sk = sk


def parse_manifest(project_dir: str):
    with open(os.path.join(project_dir, 'manifest.json')) as f:
        j = json.loads(f.read())
        j[Manifest.project_dir] = project_dir
    return j


class ZkayBlockchainInterface(metaclass=ABCMeta):
    @property
    def my_address(self) -> AddressValue:
        #debug_print(f'Requesting own address ("{self._my_address().val}")')
        return self._my_address()

    def pki_verifier_addresses(self, project_dir: str) -> List[AddressValue]:
        return self._pki_verifier_addresses(parse_manifest(project_dir))

    def req_public_key(self, address: AddressValue) -> PublicKeyValue:
        assert isinstance(address, AddressValue)
        debug_print(f'Requesting public key for address "{address.val}"')
        return self._req_public_key(address)

    def announce_public_key(self, address: AddressValue, pk: PublicKeyValue):
        assert isinstance(address, AddressValue)
        assert isinstance(pk, PublicKeyValue)
        debug_print(f'Announcing public key "{pk.val}" for address "{address.val}"')
        self._announce_public_key(address, pk)

    def req_state_var(self, contract_handle, name: str, encrypted: bool, *indices) -> Union[int, str, CipherValue]:
        assert contract_handle is not None
        debug_print(f'Requesting state variable "{name}"')
        val = self._req_state_var(contract_handle, name, *Value.unwrap_values(list(indices)))
        debug_print(f'Got value {val} for state variable "{name}"')
        return CipherValue(val) if encrypted else val

    def transact(self, contract_handle, function: str, actual_args: List, should_encrypt: List[bool]) -> Any:
        assert contract_handle is not None
        self.__check_args(actual_args, should_encrypt)
        debug_print(f'Issuing transaction for function "{function}"{str(actual_args)})')
        return self._transact(contract_handle, function, *Value.unwrap_values(actual_args))

    def deploy(self, project_dir: str, contract: str, actual_args: List, should_encrypt: List[bool]) -> Any:
        self.__check_args(actual_args, should_encrypt)
        debug_print(f'Deploying contract {contract}[{str(actual_args)}]')
        return self._deploy(parse_manifest(project_dir), contract, *Value.unwrap_values(actual_args))

    @abstractmethod
    def _my_address(self) -> AddressValue:
        pass

    @abstractmethod
    def _pki_verifier_addresses(self, manifest) -> List[AddressValue]:
        pass

    @abstractmethod
    def _req_public_key(self, address: AddressValue) -> PublicKeyValue:
        pass

    @abstractmethod
    def _announce_public_key(self, address: AddressValue, pk: PublicKeyValue) -> PublicKeyValue:
        pass

    @abstractmethod
    def _req_state_var(self, contract_handle, name: str, *indices) -> Union[int, CipherValue, AddressValue]:
        pass

    @abstractmethod
    def _transact(self, contract_handle, function: str, *actual_args) -> Any:
        pass

    @abstractmethod
    def _deploy(self, manifest, contract: str, *actual_args) -> Any:
        pass

    @staticmethod
    def __check_args(actual_args: List, should_encrypt: List[bool]):
        assert len(actual_args) == len(should_encrypt)
        for idx, arg in enumerate(actual_args):
            assert not isinstance(arg, PrivateKeyValue) and not isinstance(arg, RandomnessValue)
            assert should_encrypt[idx] == isinstance(arg, CipherValue)


class ZkayCryptoInterface(metaclass=ABCMeta):
    def __init__(self, conn: ZkayBlockchainInterface, key_dir: str = os.path.dirname(os.path.realpath(__file__))):
        self.key_dir = key_dir
        self.__my_keys = self._generate_or_load_key_pair()
        conn.announce_public_key(conn.my_address, self.local_keys.pk)

    @property
    def local_keys(self):
        return self.__my_keys

    def enc(self, plain: int, pk: PublicKeyValue) -> Tuple[CipherValue, RandomnessValue]:
        """
        Encrypts plain with the provided public key
        :param plain: plain text to encrypt
        :param pk: public key
        :return: Tuple(cipher text, randomness which was used to encrypt plain)
        """
        assert not isinstance(plain, Value) and isinstance(pk, PublicKeyValue)
        debug_print(f'Encrypting value {plain} with public key "{pk.val}"')
        return self._enc(int(plain), pk)

    def dec(self, cipher: CipherValue, sk: PrivateKeyValue) -> Tuple[int, RandomnessValue]:
        """
        Decrypts cipher with the provided secret key
        :param cipher: encrypted value
        :param sk: secret key
        :return: Tuple(plain text, randomness which was used to encrypt plain)
        """
        assert isinstance(cipher, CipherValue) and isinstance(sk, PrivateKeyValue)
        debug_print(f'Decrypting value {cipher.val} with secret key "{sk}"')
        return self._dec(cipher, sk)

    @abstractmethod
    def _generate_or_load_key_pair(self) -> KeyPair:
        pass

    @abstractmethod
    def _enc(self, plain: int, pk: PublicKeyValue) -> Tuple[CipherValue, RandomnessValue]:
        pass

    @abstractmethod
    def _dec(self, cipher: CipherValue, sk: PrivateKeyValue) -> Tuple[int, RandomnessValue]:
        pass


class ZkayKeystoreInterface:
    def __init__(self, conn: ZkayBlockchainInterface, crypto: ZkayCryptoInterface):
        self.conn = conn
        self.local_pk_store: Dict[AddressValue, PublicKeyValue] = {}
        self.my_keys = crypto.local_keys

        self.local_pk_store[conn.my_address] = self.my_keys.pk

    def getPk(self, address: AddressValue) -> PublicKeyValue:
        assert isinstance(address, AddressValue)
        debug_print(f'Requesting public key for address {address.val}')
        if address in self.local_pk_store:
            return self.local_pk_store[address]
        else:
            pk = self.conn.req_public_key(address)
            self.local_pk_store[address] = pk
            return pk

    @property
    def sk(self) -> PrivateKeyValue:
        return self.my_keys.sk

    @property
    def pk(self) -> PublicKeyValue:
        return self.my_keys.pk


class ZkayProverInterface(metaclass=ABCMeta):
    def __init__(self, proving_scheme: str = default_proving_scheme):
        self.proving_scheme = proving_scheme

    def generate_proof(self, project_dir: str, contract: str, function: str, priv_values: List[int], in_vals: Optional[List], out_vals: Optional[List[Union[int, CipherValue]]]) -> List[int]:
        for arg in priv_values:
            assert not isinstance(arg, Value) or isinstance(arg, RandomnessValue)
        manifest = parse_manifest(project_dir)
        debug_print(f'Generating proof for {contract}.{function}')
        return self._generate_proof(os.path.join(manifest[Manifest.verifier_names][f'{contract}.{function}']),
                                    Value.unwrap_values(priv_values), Value.unwrap_values(in_vals), Value.unwrap_values(out_vals))

    @abstractmethod
    def _generate_proof(self, verifier_dir: str, priv_values: List[int], in_vals: List[int], out_vals: List[int]) -> List[int]:
        pass
