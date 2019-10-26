import hashlib
from typing import List


def int_to_bytes(i, n_bytes=32):
    bytes_ = i.to_bytes(n_bytes, byteorder='big')
    return bytes_


def hash_ints_to_bytes(ints: List[int]):
    hash_ = int_to_bytes(ints[0])

    for i in range(1, len(ints)):
        next_bytes = int_to_bytes(ints[i])
        packed = hash_ + next_bytes
        hex_hash = hashlib.sha256(packed).hexdigest()
        hash_ = bytes.fromhex(hex_hash)

    return hash_


def hash_ints_to_split_int(ints: List[int]):
    bytes_hash = hash_ints_to_bytes(ints)
    part0 = bytes_hash[0:16]
    part1 = bytes_hash[16:32]
    part0 = int.from_bytes(part0, byteorder='big')
    part1 = int.from_bytes(part1, byteorder='big')
    return part0, part1
