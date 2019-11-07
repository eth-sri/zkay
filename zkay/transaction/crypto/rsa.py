import os
from typing import Tuple, Optional, List

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

import zkay.config as cfg
from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair, CipherValue, ZkayBlockchainInterface, RandomnessValue
from zkay.transaction.interface import ZkayCryptoInterface


class RandomnessProxy:
    def __init__(self) -> None:
        super().__init__()
        self.__last_rnd_bytes: Optional[bytes] = None

    def get_random_bytes(self, n: int):
        assert self.__last_rnd_bytes is None
        self.__last_rnd_bytes = get_random_bytes(n)
        return self.__last_rnd_bytes

    def retrieve_randomness(self) -> bytes:
        assert self.__last_rnd_bytes is not None
        tmp = self.__last_rnd_bytes
        self.__last_rnd_bytes = None
        return tmp


class StaticRandomnessProxy:
    def __init__(self, randombytes: bytes) -> None:
        super().__init__()
        self.__randombytes = randombytes

    def get_random_bytes(self, n: int):
        assert self.__randombytes is not None and len(self.__randombytes) == n
        tmp = self.__randombytes
        self.__randombytes = None
        return tmp

    def retrieve_randomness(self) -> bytes:
        return self.__randombytes


class RSACrypto(ZkayCryptoInterface):
    key_file = os.path.join(cfg.config_dir, 'rsa_keypair.bin')
    default_exponent = 65537 # == 0x10001

    def __init__(self, conn: ZkayBlockchainInterface, key_dir: str = os.path.dirname(os.path.realpath(__file__))):
        super().__init__(conn, key_dir)
        self.rnd_proxy = RandomnessProxy()

    def _generate_or_load_key_pair(self) -> KeyPair:
        if not os.path.exists(self.key_file):
            print(f'Key pair not found, generating new {cfg.rsa_key_bits} bit rsa key pair...')
            key = RSA.generate(cfg.rsa_key_bits, e=self.default_exponent)
            with open(self.key_file, 'wb') as f:
                f.write(key.export_key())
            print('done')
        else:
            print(f'Key not found, loading from file {self.key_file}')
            with open(self.key_file, 'rb') as f:
                key = RSA.import_key(f.read())

        modulus = key.publickey().n
        return KeyPair(PublicKeyValue(self.serialize_bigint(modulus, cfg.rsa_key_bytes)), PrivateKeyValue(key))

    def _enc(self, plain: int, pk: int, rnd: Optional[Tuple[int, ...]]) -> Tuple[List[int], List[int]]:
        pub_key = RSA.construct((pk, self.default_exponent))

        if rnd is None:
            rnd_proxy = self.rnd_proxy
        else:
            rnd_bytes = self.unpack_to_byte_array(rnd)
            rnd_proxy = StaticRandomnessProxy(rnd_bytes)
        crypto = PKCS1_OAEP.new(pub_key, hashAlgo=SHA256, randfunc=rnd_proxy.get_random_bytes)

        cipher = self.pack_byte_array(crypto.encrypt(plain.to_bytes(31, byteorder='big')))
        rnd = self.pack_byte_array(rnd_proxy.retrieve_randomness())

        return cipher, rnd

    def _dec(self, cipher: Tuple[int, ...], sk: RSA.RsaKey) -> Tuple[int, List[int]]:
        if cipher == CipherValue()[:]:
            # uninitialized value
            return 0, RandomnessValue()[:]
        else:
            crypto = PKCS1_OAEP.new(sk, hashAlgo=SHA256, randfunc=self.rnd_proxy.get_random_bytes)
            plain = int.from_bytes(crypto.decrypt(self.unpack_to_byte_array(cipher)), byteorder='big')
            rnd = self.pack_byte_array(self.rnd_proxy.retrieve_randomness())

            return plain, rnd
