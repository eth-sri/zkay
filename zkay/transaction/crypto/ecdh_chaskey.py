import secrets
from typing import Tuple, List, Any

from zkay.config import cfg
from zkay.jsnark_interface.jsnark_interface import circuit_builder_jar
from zkay.transaction.crypto.ecdh_base import EcdhBase
from zkay.utils.run_command import run_command


class EcdhChaskeyCrypto(EcdhBase):

    def _enc(self, plain: int, my_sk: int, target_pk: int) -> Tuple[List[int], List[int]]:
        # Compute shared key
        key = self._ecdh_sha256(target_pk, my_sk)
        plain_bytes = plain.to_bytes(32, byteorder='big')

        # Call java implementation
        iv = secrets.token_bytes(16)
        iv_cipher, _ = run_command(['java', '-Xms4096m', '-Xmx16384m', '-cp', f'{circuit_builder_jar}',
                                    'zkay.ChaskeyLtsCbc', 'enc', key.hex(), iv.hex(), plain_bytes.hex()])
        iv_cipher = iv + int(iv_cipher.splitlines()[-1], 16).to_bytes(32, byteorder='big')

        return self.pack_byte_array(iv_cipher, cfg.cipher_chunk_size), []

    def _dec(self, cipher: Tuple[int, ...], my_sk: Any) -> Tuple[int, List[int]]:
        # Extract sender address from cipher metadata and request corresponding public key
        sender_pk = cipher[-1]
        cipher = cipher[:-1]
        assert len(cipher) == cfg.cipher_payload_len

        # Compute shared key
        key = self._ecdh_sha256(sender_pk, my_sk)

        # Call java implementation
        iv_cipher = self.unpack_to_byte_array(cipher, cfg.cipher_chunk_size, cfg.cipher_bytes_payload)
        iv, cipher_bytes = iv_cipher[:16], iv_cipher[16:]
        plain, _ = run_command(['java', '-Xms4096m', '-Xmx16384m', '-cp', f'{circuit_builder_jar}',
                                'zkay.ChaskeyLtsCbc', 'dec', key.hex(), iv.hex(), cipher_bytes.hex()])
        plain = int(plain.splitlines()[-1], 16)

        return plain, []
