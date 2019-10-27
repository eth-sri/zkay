from typing import Tuple, Optional

from zkay.transaction.interface import CipherValue, RandomnessValue, PrivateKeyValue, PublicKeyValue, KeyPair
from zkay.transaction.interface import ZkayCryptoInterface, bn256_scalar_field


class DummyCrypto(ZkayCryptoInterface):

    def _generate_or_load_key_pair(self) -> KeyPair:
        return KeyPair(PublicKeyValue(42), PrivateKeyValue(42))

    def _enc(self, plain: int, pk: PublicKeyValue, rnd: Optional[RandomnessValue] = None) -> Tuple[CipherValue, RandomnessValue]:
        return CipherValue((plain + pk.val) % bn256_scalar_field), RandomnessValue(69)

    def _dec(self, cipher: CipherValue, sk: PrivateKeyValue) -> Tuple[int, RandomnessValue]:
        return (cipher.val - sk.val) % bn256_scalar_field, RandomnessValue(69)
