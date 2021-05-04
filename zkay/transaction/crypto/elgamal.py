from typing import Tuple, List, Any, Union

from Crypto.Random.random import randrange

from zkay.transaction.crypto import babyjubjub
from zkay.transaction.crypto.params import CryptoParams
from zkay.transaction.interface import ZkayHomomorphicCryptoInterface
from zkay.transaction.types import KeyPair, CipherValue


class ElgamalCrypto(ZkayHomomorphicCryptoInterface):
    params = CryptoParams('paillier')

    def _generate_or_load_key_pair(self, address: str) -> KeyPair:
        # TODO implement
        pass

    def _enc(self, plain: int, _: int, target_pk: int) -> Tuple[List[int], List[int]]:
        pk = self.serialize_pk(target_pk, self.params.key_bytes)
        r = randrange(babyjubjub.CURVE_ORDER)
        cipher_chunks = self._enc_with_rand(plain, r, pk)
        return cipher_chunks, [r]

    def _dec(self, cipher: Tuple[int, ...], sk: Any) -> Tuple[int, List[int]]:
        # TODO implement
        pass

    def do_op(self, op: str, public_key: List[int], *args: Union[CipherValue, int]) -> List[int]:
        # TODO implement
        pass

    def _enc_with_rand(self, plain: int, random: int, pk: List[int]) -> List[int]:
        plain_embedded = babyjubjub.Point.GENERATOR * babyjubjub.Fr(plain)
        shared_secret = babyjubjub.Point(babyjubjub.Fq(pk[0]), babyjubjub.Fq(pk[1])) * babyjubjub.Fr(random)
        c1 = babyjubjub.Point.GENERATOR * babyjubjub.Fr(random)
        c2 = plain_embedded + shared_secret
        return [c1.u, c1.v, c2.u, c2.v]
