import hashlib
from unittest import TestCase

from zkay.transaction.legacy.encoding_helper import int_to_bytes, hash_ints_to_split_int, hash_ints_to_bytes


class TestEncodingHelper(TestCase):

    def test_hash_5(self):
        # check consistency with https://blog.decentriq.ch/proving-hash-pre-image-zksnarks-zokrates/
        bytes_ = int_to_bytes(5, 64)
        h = hashlib.sha256(bytes_).hexdigest()
        self.assertEqual(h, 'c6481e22c5ff4164af680b8cfaa5e8ed3120eeff89c4f307c4a6faaae059ce10')

    def test_bytes32_10(self):
        # compare to reference gathered by running solidity

        bytes_ = int_to_bytes(10)
        hex_ = bytes_.hex()
        self.assertEqual(hex_, '000000000000000000000000000000000000000000000000000000000000000a')

    def test_hash_ints_to_bytes(self):
        # compare to reference gathered by running solidity
        hash_bytes = hash_ints_to_bytes([10, 20])
        hash_hex = hash_bytes.hex()
        self.assertEqual(hash_hex, 'e64518ee7aa7578340f43207b116d6493a975f8ef89b3ceb1bb8b6cd30c9bcca')

    def test_hash(self):
        part0, part1 = hash_ints_to_split_int([10, 20])
        self.assertEqual(part0, 306081213185862194986414395801732568649)
        self.assertEqual(part1, 77881198737415257151260349207509843146)
