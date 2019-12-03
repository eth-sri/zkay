from typing import Tuple, List

from zkay.config import cfg
from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair, RandomnessValue
from zkay.transaction.interface import ZkayCryptoInterface


class DummyCrypto(ZkayCryptoInterface):
    def _generate_or_load_key_pair(self, address: str) -> KeyPair:
        aint = int(address, 16)
        return KeyPair(PublicKeyValue(self.serialize_bigint(aint, cfg.key_bytes)), PrivateKeyValue(aint))

    def _enc(self, plain: int, pk: int) -> Tuple[List[int], List[int]]:
        cipher = (plain + pk) % bn128_scalar_field
        return self.pack_byte_array(cipher.to_bytes(cfg.key_bytes, byteorder='big')), list(RandomnessValue()[:])

    def _dec(self, cipher: Tuple[int, ...], sk: int) -> Tuple[int, List[int]]:
        plain = (int.from_bytes(self.unpack_to_byte_array(cipher, cfg.key_bytes), byteorder='big') - sk) % bn128_scalar_field
        return plain, list(RandomnessValue()[:])
