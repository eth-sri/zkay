from random import Random, random
from typing import Tuple, List

from Crypto.Math.Primality import generate_probable_prime

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.crypto.params import CryptoParams
from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair, RandomnessValue
from zkay.transaction.interface import ZkayCryptoInterface


class DummyHomCrypto(ZkayCryptoInterface):
    params = CryptoParams('dummy-hom')

    def _generate_or_load_key_pair(self, address: str) -> KeyPair:
        seed = int(address, 16)
        rng = Random(seed)
        def rand_bytes(n: int) -> bytes:
            return bytes([rng.randrange(256) for _ in range(n)])

        pk = int(generate_probable_prime(exact_bits=self.params.key_bits, randfunc=rand_bytes))
        return KeyPair(PublicKeyValue(self.serialize_pk(pk, self.params.key_bytes), params=self.params),
                       PrivateKeyValue(pk))

    def _enc(self, plain: int, _: int, target_pk: int):
        cipher = (plain * target_pk) % bn128_scalar_field
        return [cipher], list(RandomnessValue(params=self.params)[:])

    def _dec(self, cipher: Tuple[int, ...], sk: int) -> Tuple[int, List[int]]:
        key_inv = pow(sk, -1, bn128_scalar_field)
        plain = (cipher[0] * key_inv) % bn128_scalar_field
        return plain, list(RandomnessValue(params=self.params)[:])
