from random import Random
from typing import Tuple, List, Union

from Crypto.Math.Primality import generate_probable_prime

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.crypto.params import CryptoParams
from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair, RandomnessValue, \
    ZkayHomomorphicCryptoInterface
from zkay.transaction.types import CipherValue


class DummyHomCrypto(ZkayHomomorphicCryptoInterface):
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
        plain = plain % bn128_scalar_field  # handle negative values
        cipher = (plain * target_pk + 1) % bn128_scalar_field
        return [cipher], list(RandomnessValue(params=self.params)[:])

    def _dec(self, cipher: Tuple[int, ...], sk: int) -> Tuple[int, List[int]]:
        key_inv = pow(sk, -1, bn128_scalar_field)
        plain = ((cipher[0] - 1) * key_inv) % bn128_scalar_field
        if plain > bn128_scalar_field // 2:
            plain = plain - bn128_scalar_field
        return plain, list(RandomnessValue(params=self.params)[:])

    def do_op(self, op: str, public_key: Union[List[int], int], *args: Union[CipherValue]) -> List[int]:
        def deserialize(operand: Union[CipherValue]) -> int:
            val = operand[0]
            return val - 1 if val != 0 else 0

        operands = [deserialize(arg) for arg in args]
        if op == 'sign-':
            result = -operands[0]
        elif op == '+':
            result = operands[0] + operands[1]
        elif op == '-':
            result = operands[0] - operands[1]
        elif op == '*':
            result = operands[0] * operands[1]
        else:
            raise ValueError(f'Unsupported operation {op}')
        return [(result + 1) % bn128_scalar_field]
