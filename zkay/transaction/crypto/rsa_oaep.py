from typing import Tuple, Optional, List

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

import zkay.config as cfg
from zkay.transaction.crypto.rsa_base import RSACrypto, PersistentLocals, StaticRandomFunc
from zkay.transaction.interface import CipherValue, RandomnessValue


class RSAOAEPCrypto(RSACrypto):
    def _enc(self, plain: int, pk: int, rnd: Optional[Tuple[int, ...]]) -> Tuple[List[int], List[int]]:
        pub_key = RSA.construct((pk, self.default_exponent))

        if rnd is None:
            randfunc = get_random_bytes
        else:
            randbytes = self.unpack_to_byte_array(rnd, cfg.rnd_bytes)
            randfunc = StaticRandomFunc(randbytes).get_random_bytes

        encrypt = PersistentLocals(PKCS1_OAEP.new(pub_key, hashAlgo=SHA256, randfunc=randfunc).encrypt)
        cipher_bytes = encrypt(plain.to_bytes(cfg.pack_chunk_size, byteorder='big'))
        cipher = self.pack_byte_array(cipher_bytes)

        rnd_bytes = encrypt.locals['ros']
        rnd = self.pack_byte_array(rnd_bytes)

        return cipher, rnd

    def _dec(self, cipher: Tuple[int, ...], sk: RSA.RsaKey) -> Tuple[int, List[int]]:
        if cipher == CipherValue()[:]:
            # uninitialized value
            return 0, RandomnessValue()[:]
        else:
            decrypt = PersistentLocals(PKCS1_OAEP.new(sk, hashAlgo=SHA256).decrypt)
            plain = int.from_bytes(decrypt(self.unpack_to_byte_array(cipher, cfg.key_bytes)), byteorder='big')

            rnd_bytes = decrypt.locals['seed']
            rnd = self.pack_byte_array(rnd_bytes)

            return plain, rnd
