import math
import re

from zkay.transaction.crypto.meta import cryptoparams


class CryptoParams:

    def __init__(self, crypto_name: str):
        self.crypto_name = crypto_name

    def __eq__(self, other):
        return isinstance(other, CryptoParams) and self.crypto_name == other.crypto_name

    def __hash__(self):
        return self.crypto_name.__hash__()

    @property
    def identifier_name(self) -> str:
        return re.sub('[^a-zA-Z0-9$_]', '_', self.crypto_name).title()

    @property
    def key_bits(self) -> int:
        return cryptoparams[self.crypto_name]['key_bits']

    @property
    def key_bytes(self) -> int:
        return self.key_bits // 8

    @property
    def key_len(self) -> int:
        return 1 if self.is_symmetric_cipher() else int(math.ceil(self.key_bytes / self.cipher_chunk_size))

    @property
    def rnd_bytes(self) -> int:
        return cryptoparams[self.crypto_name]['rnd_bytes']

    @property
    def rnd_chunk_size(self) -> int:
        return cryptoparams[self.crypto_name]['rnd_chunk_size']

    @property
    def randomness_len(self) -> int:
        return 0 if self.is_symmetric_cipher() else int(math.ceil(self.rnd_bytes / self.rnd_chunk_size))

    @property
    def cipher_bytes_payload(self) -> int:
        return cryptoparams[self.crypto_name]['cipher_payload_bytes']

    def is_symmetric_cipher(self) -> bool:
        return cryptoparams[self.crypto_name]['symmetric']

    @property
    def cipher_payload_len(self) -> int:
        return int(math.ceil(self.cipher_bytes_payload / self.cipher_chunk_size))

    @property
    def cipher_len(self) -> int:
        if self.is_symmetric_cipher():
            return self.cipher_payload_len + 1 # Additional uint to store sender address
        else:
            return self.cipher_payload_len

    @property
    def cipher_chunk_size(self) -> int:
        return cryptoparams[self.crypto_name]['cipher_chunk_size']

    @property
    def enc_signed_as_unsigned(self) -> int:
        return cryptoparams[self.crypto_name]['enc_signed_as_unsigned']
