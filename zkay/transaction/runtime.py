from zkay.config import default_snark_backend
from zkay.transaction.interface import ZkayBlockchainInterface, ZkayCryptoInterface, ZkayKeystoreInterface, ZkayProverInterface
from zkay.transaction.blockchain import Web3TesterBlockchain
from zkay.transaction.crypto import DummyCrypto, RSACrypto
from zkay.transaction.keystore import SimpleKeystore
from zkay.transaction.prover import ZokratesProver, JsnarkProver


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
            Runtime.__crypto = RSACrypto(Runtime.blockchain())
        return Runtime.__crypto

    @staticmethod
    def keystore() -> ZkayKeystoreInterface:
        if Runtime.__keystore is None:
            Runtime.__keystore = SimpleKeystore(Runtime.blockchain(), Runtime.crypto())
        return Runtime.__keystore

    @staticmethod
    def prover() -> ZkayProverInterface:
        if Runtime.__prover is None:
            if default_snark_backend == 'zokrates':
                Runtime.__prover = ZokratesProver()
            elif default_snark_backend == 'jsnark':
                Runtime.__prover = JsnarkProver()
            else:
                raise ValueError(f'Invalid prover backend {default_snark_backend}')
        return Runtime.__prover
