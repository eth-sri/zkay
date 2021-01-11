from typing import Tuple, List

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from zkay.transaction.crypto.params import CryptoParams
from zkay.transaction.crypto.rsa_base import RSACrypto, PersistentLocals


class RSAPKCS15Crypto(RSACrypto):
    params = CryptoParams('rsa-pkcs1.5')

    def _enc(self, plain: int, _: int, target_pk: int) -> Tuple[List[int], List[int]]:
        pub_key = RSA.construct((target_pk, self.default_exponent))
        encrypt = PersistentLocals(PKCS1_v1_5.new(pub_key).encrypt)

        cipher_bytes = encrypt(plain.to_bytes(32, byteorder='big'))
        cipher = self.pack_byte_array(cipher_bytes, self.params.cipher_chunk_size)

        rnd_bytes = encrypt.locals['ps']
        assert len(rnd_bytes) == self.params.rnd_bytes
        rnd = self.pack_byte_array(rnd_bytes, self.params.rnd_chunk_size)

        return cipher, rnd

    def _dec(self, cipher: Tuple[int, ...], sk: RSA.RsaKey) -> Tuple[int, List[int]]:
        decrypt = PersistentLocals(PKCS1_v1_5.new(sk).decrypt)
        cipher_bytes = self.unpack_to_byte_array(cipher, self.params.cipher_chunk_size, self.params.cipher_bytes_payload)
        ret = decrypt(cipher_bytes, None)
        if ret is None:
            raise RuntimeError("Tried to decrypt invalid cipher text")
        plain = int.from_bytes(ret, byteorder='big')

        rnd_bytes = decrypt.locals['em'][2:decrypt.locals['sep']]
        assert len(rnd_bytes) == self.params.rnd_bytes
        rnd = self.pack_byte_array(rnd_bytes, self.params.rnd_chunk_size)

        return plain, rnd
