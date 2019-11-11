from typing import Tuple, Optional, List

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

import zkay.config as cfg
from zkay.transaction.crypto.rsa_base import RSACrypto, StaticRandomFunc, PersistentLocals
from zkay.transaction.interface import CipherValue, RandomnessValue


class RSAPKCS15Crypto(RSACrypto):

    def _enc(self, plain: int, pk: int, rnd: Optional[Tuple[int, ...]]) -> Tuple[List[int], List[int]]:
        pub_key = RSA.construct((pk, self.default_exponent))

        if rnd is None:
            randfunc = get_random_bytes
        else:
            randbytes = self.unpack_to_byte_array(rnd, cfg.rnd_bytes)
            randfunc = StaticRandomFunc(randbytes).get_random_bytes

        encrypt = PersistentLocals(PKCS1_v1_5.new(pub_key, randfunc=randfunc).encrypt)

        cipher_bytes = encrypt(plain.to_bytes(cfg.pack_chunk_size, byteorder='big'))
        cipher = self.pack_byte_array(cipher_bytes)

        rnd_bytes = encrypt.locals['ps']
        assert len(rnd_bytes) == cfg.rnd_bytes
        rnd = self.pack_byte_array(rnd_bytes)

        return cipher, rnd

    def _dec(self, cipher: Tuple[int, ...], sk: RSA.RsaKey) -> Tuple[int, List[int]]:
        if cipher == CipherValue()[:]:
            # uninitialized value
            return 0, RandomnessValue()[:]
        else:
            decrypt = PersistentLocals(PKCS1_v1_5.new(sk).decrypt)
            ret = decrypt(self.unpack_to_byte_array(cipher, cfg.key_bytes), None)
            if ret is None:
                raise RuntimeError("Tried to decrypt invalid cipher text")
            plain = int.from_bytes(ret, byteorder='big')

            rnd_bytes = decrypt.locals['em'][2:decrypt.locals['sep']]
            assert len(rnd_bytes) == cfg.rnd_bytes
            rnd = self.pack_byte_array(rnd_bytes)

            return plain, rnd
