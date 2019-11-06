from typing import Tuple, Optional

from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair, CipherValue
from zkay.transaction.interface import ZkayCryptoInterface
from zkay.compiler.privacy.library_contracts import bn128_scalar_field


class DummyCrypto(ZkayCryptoInterface):

    def _generate_or_load_key_pair(self) -> KeyPair:
        return KeyPair(PublicKeyValue([42, 0]), PrivateKeyValue([42, 0]))

    def _enc(self, plain: int, pk: Tuple[int, ...], rnd: Optional[Tuple[int, ...]]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
        if rnd is not None:
            assert rnd == (69, 0), f'rnd was {rnd}'
        cipher = (plain + pk[0]) % bn128_scalar_field
        return (cipher, 0), (69, 0)

    def _dec(self, cipher: Tuple[int, ...], sk: Tuple[int, ...]) -> Tuple[int, Tuple[int, ...]]:
        if cipher == CipherValue()[:]:
            # uninitialized value
            plain = 0
        else:
            plain = (cipher[0] - sk[0]) % bn128_scalar_field
        return plain, (69, 0)
