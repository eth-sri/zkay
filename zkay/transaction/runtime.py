from zkay.transaction.interface import ZkayBlockchainInterface, ZkayCryptoInterface, ZkayKeystoreInterface, ZkayProverInterface
from zkay.transaction.blockchain import Web3TesterBlockchain
from zkay.transaction.crypto import DummyCrypto
from zkay.transaction.keystore import SimpleKeystore
from zkay.transaction.prover import ZokratesProver


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
            Runtime.__crypto = DummyCrypto(Runtime.blockchain())
        return Runtime.__crypto

    @staticmethod
    def keystore() -> ZkayKeystoreInterface:
        if Runtime.__keystore is None:
            Runtime.__keystore = SimpleKeystore(Runtime.blockchain(), Runtime.crypto())
        return Runtime.__keystore

    @staticmethod
    def prover() -> ZkayProverInterface:
        if Runtime.__prover is None:
            Runtime.__prover = ZokratesProver()
        return Runtime.__prover
