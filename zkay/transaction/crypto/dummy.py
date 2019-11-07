from typing import Tuple, Optional, List

import zkay.config as cfg

from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair, CipherValue, RandomnessValue
from zkay.transaction.interface import ZkayCryptoInterface
from zkay.compiler.privacy.library_contracts import bn128_scalar_field


class DummyCrypto(ZkayCryptoInterface):

    def _generate_or_load_key_pair(self) -> KeyPair:
        return KeyPair(PublicKeyValue(self.serialize_bigint(42, cfg.rsa_key_bytes)), PrivateKeyValue(42))

    def _enc(self, plain: int, pk: int, rnd: Optional[Tuple[int, ...]]) -> Tuple[List[int], List[int]]:
        if rnd is not None:
            assert rnd == RandomnessValue()[:], f'rnd was {rnd}'
        cipher = (plain + pk) % bn128_scalar_field
        return self.pack_byte_array(cipher.to_bytes(cfg.rsa_key_bytes, byteorder='big')), list(RandomnessValue()[:])

    def _dec(self, cipher: Tuple[int, ...], sk: int) -> Tuple[int, List[int]]:
        if cipher == CipherValue()[:]:
            # uninitialized value
            plain = 0
        else:
            plain = (int.from_bytes(self.unpack_to_byte_array(cipher), byteorder='big') - sk) % bn128_scalar_field
        return plain, list(RandomnessValue()[:])
