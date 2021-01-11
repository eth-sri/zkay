import os
import secrets

from zkay.config import cfg
from zkay.jsnark_interface.jsnark_interface import circuit_builder_jar
from zkay.transaction.interface import PrivateKeyValue, PublicKeyValue, KeyPair
from zkay.transaction.interface import ZkayCryptoInterface
from zkay.utils.run_command import run_command


class EcdhBase(ZkayCryptoInterface):

    @staticmethod
    def _gen_keypair(rnd: bytes):
        keys, _ = run_command(['java', '-Xms4096m', '-Xmx16384m', '-cp', f'{circuit_builder_jar}', 'zkay.ZkayECDHGenerator', rnd.hex()])
        keys = keys.splitlines()[-2:]
        return int(keys[0], 16), int(keys[1], 16)

    @staticmethod
    def _ecdh_sha256(other_pk: int, my_sk: int):
        ret, _ = run_command(['java', '-Xms4096m', '-Xmx16384m', '-cp', f'{circuit_builder_jar}', 'zkay.ZkayECDHGenerator', hex(my_sk)[2:], hex(other_pk)[2:]])
        key = ret.splitlines()[-1]
        return int(key, 16).to_bytes(16, byteorder='big')

    def _generate_or_load_key_pair(self, address: str) -> KeyPair:
        key_file = os.path.join(cfg.data_dir, 'keys', f'ec_{address}.bin')
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        if not os.path.exists(key_file):
            # Generate fresh randomness for ec private key
            print(f'Key pair not found, generating new EC secret...')
            rnd = secrets.token_bytes(32)

            # Store randomness so that address will have the same key every time
            with open(key_file, 'wb') as f:
                f.write(rnd)
            print('done')
        else:
            # Restore saved randomness
            print(f'EC secret found, loading from file {key_file}')
            with open(key_file, 'rb') as f:
                rnd = f.read()

        # Derive keys from randomness
        pk, sk = self._gen_keypair(rnd)

        return KeyPair(PublicKeyValue([pk], params=self.params), PrivateKeyValue(sk))
