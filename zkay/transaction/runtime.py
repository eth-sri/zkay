from zkay.config import cfg
from zkay.transaction.blockchain.web3py import Web3IpcBlockchain, Web3WebsocketBlockchain, Web3HttpBlockchain, Web3CustomBlockchain, \
    Web3HttpGanacheBlockchain
from zkay.transaction.crypto.rsa_oaep import RSAOAEPCrypto
from zkay.transaction.crypto.rsa_pkcs15 import RSAPKCS15Crypto

from zkay.transaction.interface import ZkayBlockchainInterface, ZkayCryptoInterface, ZkayKeystoreInterface, ZkayProverInterface
from zkay.transaction.blockchain import Web3TesterBlockchain
from zkay.transaction.crypto.dummy import DummyCrypto
from zkay.transaction.keystore import SimpleKeystore
from zkay.transaction.prover import JsnarkProver

_crypto_classes = {
    'dummy': DummyCrypto,
    'rsa-pkcs1.5': RSAPKCS15Crypto,
    'rsa-oaep': RSAOAEPCrypto
}

_prover_classes = {
    'jsnark': JsnarkProver
}

_blockchain_classes = {
    'w3-eth-tester': Web3TesterBlockchain,
    'w3-ganache': Web3HttpGanacheBlockchain,
    'w3-ipc': Web3IpcBlockchain,
    'w3-websocket': Web3WebsocketBlockchain,
    'w3-http': Web3HttpBlockchain,
    'w3-custom': Web3CustomBlockchain
}


class Runtime:
    """
    Provides global access to singleton runtime API backend instances.
    See interface.py for more information.

    The global configuration in config.py determines which backends are made available via the Runtime class.
    """

    __blockchain = None
    __crypto = None
    __keystore = None
    __prover = None

    @staticmethod
    def reset():
        """
        Reboot the runtime.

        When a new backend is selected in the configuration, it will only be loaded after a runtime reset.
        """
        Runtime.__blockchain = None
        Runtime.__crypto = None
        Runtime.__keystore = None
        Runtime.__prover = None

    @staticmethod
    def blockchain() -> ZkayBlockchainInterface:
        """Return singleton object which implements ZkayBlockchainInterface."""
        if Runtime.__blockchain is None:
            Runtime.__blockchain = _blockchain_classes[cfg.blockchain_backend]()
            from zkay.transaction.types import AddressValue
            AddressValue.get_balance = Runtime.__blockchain.get_balance
        return Runtime.__blockchain

    @staticmethod
    def crypto() -> ZkayCryptoInterface:
        """Return singleton object which implements ZkayCryptoInterface."""
        if Runtime.__crypto is None:
            Runtime.__crypto = _crypto_classes[cfg.crypto_backend]()
        return Runtime.__crypto

    @staticmethod
    def keystore() -> ZkayKeystoreInterface:
        """Return singleton object which implements ZkayKeystoreInterface."""
        if Runtime.__keystore is None:
            Runtime.__keystore = SimpleKeystore(Runtime.blockchain())
        return Runtime.__keystore

    @staticmethod
    def prover() -> ZkayProverInterface:
        """Return singleton object which implements ZkayProverInterface."""
        if Runtime.__prover is None:
            Runtime.__prover = _prover_classes[cfg.snark_backend]()
        return Runtime.__prover
