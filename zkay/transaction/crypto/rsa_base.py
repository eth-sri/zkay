import os
import sys

from Crypto.PublicKey import RSA

from zkay.config import cfg
from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair, ZkayBlockchainInterface
from zkay.transaction.interface import ZkayCryptoInterface


# persistent_locals2 has been co-authored with Andrea Maffezzoli
# http://code.activestate.com/recipes/577283-decorator-to-expose-local-variables-of-a-function-/
# (hack to get local variables of called library function, used to extract randomness)
class PersistentLocals(object):
    def __init__(self, func):
        self._locals = {}
        self.func = func

    def __call__(self, *args, **kwargs):
        def tracer(frame, event, arg):
            if event == 'return':
                self._locals = frame.f_locals.copy()

        # tracer is activated on next call, return or exception
        sys.setprofile(tracer)
        try:
            # trace the function call
            res = self.func(*args, **kwargs)
        finally:
            # disable tracer and replace with old one
            sys.setprofile(None)
        return res

    def clear_locals(self):
        self._locals = {}

    @property
    def locals(self):
        return self._locals


class StaticRandomFunc:
    def __init__(self, rnd_bytes) -> None:
        self.rnd_bytes = rnd_bytes

    def get_random_bytes(self, n):
        assert len(self.rnd_bytes) >= n
        ret = self.rnd_bytes[:n]
        self.rnd_bytes = self.rnd_bytes[n:]
        return ret


class RSACrypto(ZkayCryptoInterface):
    key_file = os.path.join(cfg.config_dir, 'rsa_keypair.bin')
    default_exponent = 65537 # == 0x10001

    def __init__(self, conn: ZkayBlockchainInterface, key_dir: str = os.path.dirname(os.path.realpath(__file__))):
        super().__init__(conn, key_dir)

    def _generate_or_load_key_pair(self) -> KeyPair:
        if not os.path.exists(self.key_file):
            print(f'Key pair not found, generating new {cfg.key_bits} bit rsa key pair...')
            key = RSA.generate(cfg.key_bits, e=self.default_exponent)
            with open(self.key_file, 'wb') as f:
                f.write(key.export_key())
            print('done')
        else:
            print(f'Key pair found, loading from file {self.key_file}')
            with open(self.key_file, 'rb') as f:
                key = RSA.import_key(f.read())

        modulus = key.publickey().n
        return KeyPair(PublicKeyValue(self.serialize_bigint(modulus, cfg.key_bytes)), PrivateKeyValue(key))
