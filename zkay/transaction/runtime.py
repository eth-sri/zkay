from zkay.config import cfg
from zkay.transaction.crypto.rsa_oaep import RSAOAEPCrypto
from zkay.transaction.crypto.rsa_pkcs15 import RSAPKCS15Crypto

from zkay.transaction.interface import ZkayBlockchainInterface, ZkayCryptoInterface, ZkayKeystoreInterface, ZkayProverInterface
from zkay.transaction.blockchain import Web3TesterBlockchain
from zkay.transaction.crypto.dummy import DummyCrypto
from zkay.transaction.keystore import SimpleKeystore
from zkay.transaction.prover import ZokratesProver, JsnarkProver


def get_crypto_class(name: str):
    if name == 'rsa_pkcs1_5':
        return RSAPKCS15Crypto
    elif name == 'rsa_oaep':
        return RSAOAEPCrypto
    elif name == 'dummy':
        return DummyCrypto
    else:
        raise ValueError(f'Invalid crypto backend {name}')


def get_prover_class(name: str):
    if name == 'zokrates':
        return ZokratesProver
    elif name == 'jsnark':
        return JsnarkProver
    else:
        raise ValueError(f'Invalid prover backend {name}')


class Runtime:
    __blockchain = None
    __crypto = None
    __keystore = None
    __prover = None

    @staticmethod
    def blockchain() -> ZkayBlockchainInterface:
        if Runtime.__blockchain is None:
            Runtime.__blockchain = Web3TesterBlockchain()
        return Runtime.__blockchain

    @staticmethod
    def crypto() -> ZkayCryptoInterface:
        if Runtime.__crypto is None:
            Runtime.__crypto = get_crypto_class(cfg.crypto_backend)(Runtime.blockchain())
        return Runtime.__crypto

    @staticmethod
    def keystore() -> ZkayKeystoreInterface:
        if Runtime.__keystore is None:
            Runtime.__keystore = SimpleKeystore(Runtime.blockchain(), Runtime.crypto())
        return Runtime.__keystore

    @staticmethod
    def prover() -> ZkayProverInterface:
        if Runtime.__prover is None:
            Runtime.__prover = get_prover_class(cfg.snark_backend)()
        return Runtime.__prover
