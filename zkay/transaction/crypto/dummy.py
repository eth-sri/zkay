from typing import Tuple, Optional

from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair
from zkay.transaction.interface import ZkayCryptoInterface, bn256_scalar_field


class DummyCrypto(ZkayCryptoInterface):

    def _generate_or_load_key_pair(self) -> KeyPair:
        return KeyPair(PublicKeyValue(42), PrivateKeyValue(42))

    def _enc(self, plain: int, pk: int, rnd: Optional[int]) -> Tuple[int, int]:
        if rnd is not None:
            assert rnd == 69, f'rnd was {rnd}'
        cipher = (plain + pk) % bn256_scalar_field
        return cipher, rnd if rnd is not None else 69

    def _dec(self, cipher: int, sk: int) -> Tuple[int, int]:
        return (cipher - sk) % bn256_scalar_field, 69
