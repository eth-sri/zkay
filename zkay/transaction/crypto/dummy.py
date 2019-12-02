from typing import Tuple, List

import zkay.config as cfg
from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair, RandomnessValue
from zkay.transaction.interface import ZkayCryptoInterface


class DummyCrypto(ZkayCryptoInterface):

    def _generate_or_load_key_pair(self) -> KeyPair:
        return KeyPair(PublicKeyValue(self.serialize_bigint(42, cfg.key_bytes)), PrivateKeyValue(42))

    def _enc(self, plain: int, pk: int) -> Tuple[List[int], List[int]]:
        cipher = (plain + pk) % bn128_scalar_field
        return self.pack_byte_array(cipher.to_bytes(cfg.key_bytes, byteorder='big')), list(RandomnessValue()[:])

    def _dec(self, cipher: Tuple[int, ...], sk: int) -> Tuple[int, List[int]]:
        plain = (int.from_bytes(self.unpack_to_byte_array(cipher, cfg.key_bytes), byteorder='big') - sk) % bn128_scalar_field
        return plain, list(RandomnessValue()[:])
