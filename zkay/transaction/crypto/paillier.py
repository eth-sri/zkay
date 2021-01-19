import os
from math import gcd
from typing import Tuple, Any, List, Union

from Crypto.Math.Primality import generate_probable_prime
from Crypto.Random.random import getrandbits

from zkay.config import cfg
from zkay.transaction.crypto.params import CryptoParams
from zkay.transaction.interface import ZkayHomomorphicCryptoInterface
from zkay.transaction.types import KeyPair, PublicKeyValue, PrivateKeyValue


class PaillierCrypto(ZkayHomomorphicCryptoInterface):
    params = CryptoParams('paillier')

    def _generate_or_load_key_pair(self, address: str) -> KeyPair:
        key_file = os.path.join(cfg.data_dir, 'keys', f'paillier_{address}.bin')
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        if not os.path.exists(key_file):
            print(f'Key pair not found, generating new Paillier secret...')
            pk, sk = self._generate_key_pair()
            self._write_key_pair(key_file, pk, sk)
            print('Done')
        else:
            # Restore saved key pair
            print(f'Paillier secret found, loading from file {key_file}')
            pk, sk = self._read_key_pair(key_file)

        return KeyPair(PublicKeyValue(pk, params=self.params), PrivateKeyValue(sk))

    def _write_key_pair(self, key_file: str, pk: List[int], sk: List[int]):
        with open(key_file, 'wb') as f:
            f.write(len(pk).to_bytes(4, byteorder='big'))
            for p in pk:
                f.write(p.to_bytes(self.params.cipher_chunk_size, byteorder='big'))
            f.write(len(sk).to_bytes(4, byteorder='big'))
            for s in sk:
                f.write(s.to_bytes(self.params.cipher_chunk_size, byteorder='big'))

    def _read_key_pair(self, key_file: str) -> Tuple[List[int], List[int]]:
        pk = []
        sk = []
        with open(key_file, 'rb') as f:
            pk_len = int.from_bytes(f.read(4), byteorder='big')
            for _ in range(pk_len):
                pk.append(int.from_bytes(f.read(self.params.cipher_chunk_size), byteorder='big'))
            sk_len = int.from_bytes(f.read(4), byteorder='big')
            for _ in range(sk_len):
                sk.append(int.from_bytes(f.read(self.params.cipher_chunk_size), byteorder='big'))
        return pk, sk

    def _generate_key_pair(self) -> Tuple[List[int], List[int]]:
        n_bits = self.params.key_bits
        pq_bits = (n_bits + 1) // 2

        while True:
            p = int(generate_probable_prime(exact_bits=pq_bits))
            q = int(generate_probable_prime(exact_bits=pq_bits))
            n = p * q
            if p != q and n.bit_length() == n_bits:
                break

        n_chunks = self.serialize_pk(n, self.params.key_bytes)
        p_chunks = self.serialize_pk(p, self.params.key_bytes)
        q_chunks = self.serialize_pk(q, self.params.key_bytes)

        return n_chunks, p_chunks + q_chunks

    def _enc(self, plain: int, _: int, target_pk: int) -> Tuple[List[int], List[int]]:
        n = target_pk
        n_sqr = n * n
        plain = plain % n  # handle negative numbers
        while True:
            random = getrandbits(n.bit_length())
            if 0 < random < n and (gcd(random, n) == 1):
                break

        g_pow_plain = n * plain + 1
        rand_pow_n = pow(random, n, n_sqr)
        cipher = (g_pow_plain * rand_pow_n) % n_sqr

        cipher_chunks = self.serialize_pk(cipher, self.params.cipher_bytes_payload)
        random_chunks = self.serialize_pk(random, self.params.rnd_bytes)

        return cipher_chunks, random_chunks

    def _dec(self, cipher: Tuple[int, ...], sk: Any) -> Tuple[int, List[int]]:
        p = self.deserialize_pk(sk[:self.params.key_len])
        q = self.deserialize_pk(sk[self.params.key_len:])
        n = p * q
        n_sqr = n * n
        lambda_ = (p - 1) * (q - 1)
        lambda_inv = pow(lambda_, -1, n)
        c = self.deserialize_pk(cipher)

        # Compute the plaintext: plain = L(cipher^lambda mod n^2) / lambda mod n
        c_pow_lambda = pow(c, lambda_, n_sqr)
        l = (c_pow_lambda - 1) // n
        plain = (l * lambda_inv) % n

        # Compute the randomness that was used
        # Fortunately, this has been asked and answered on stackexchange: https://math.stackexchange.com/a/114142
        generator = n + 1
        g_pow_plain_inv = pow(generator, -plain, n_sqr)
        rand_pow_n = (c * g_pow_plain_inv) % n_sqr
        p_inv = pow(p, -1, q - 1)  # Inverse of p modulo q-1
        q_inv = pow(q, -1, p - 1)  # Inverse of q modulo p-1
        c_pow_p_inv = pow(rand_pow_n, p_inv, q)
        c_pow_q_inv = pow(rand_pow_n, q_inv, p)
        # random == c_pow_q_inv mod p
        # random == c_pow_p_inv mod q
        # Compute random using the Chinese Remainder Theorem
        y_1 = pow(q, -1, p)
        y_2 = pow(p, -1, q)
        w_1 = (y_1 * q) % n
        w_2 = (y_2 * p) % n

        random = (c_pow_q_inv * w_1 + c_pow_p_inv * w_2) % n
        random_chunks = self.serialize_pk(random, self.params.rnd_bytes)

        # Handle possible negative plaintexts
        if plain > n // 2:
            plain = plain - n

        return plain, random_chunks

    def do_op(self, op: str, public_key: Union[List[int], int], *args: Union[List[int], int]) -> List[int]:
        n = self.deserialize_pk(public_key)
        n_sqr = n * n

        def deserialize(operand: Union[List[int], int]) -> int:
            if isinstance(operand, List):
                val = self.deserialize_pk(operand[:])
                return val if val != 0 else 1  # If ciphertext is 0, return 1 == Enc(0, 0)
            else:
                return operand  # Return plaintext arguments as-is
        operands = [deserialize(arg) for arg in args]

        if op == 'sign-':
            result = pow(operands[0], -1, n_sqr)
        elif op == '+':
            result = (operands[0] * operands[1]) % n_sqr
        elif op == '-':
            result = (operands[0] * pow(operands[1], -1, n_sqr)) % n_sqr
        elif op == '*' and isinstance(args[1], int):
            result = pow(operands[0], operands[1], n_sqr)
        elif op == '*' and isinstance(args[0], int):
            result = pow(operands[1], operands[0], n_sqr)
        else:
            raise ValueError(f'Unsupported operation {op}')

        return self.serialize_pk(result, self.params.cipher_bytes_payload)
