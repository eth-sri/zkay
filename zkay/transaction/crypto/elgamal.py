from zkay.transaction.crypto.params import CryptoParams
from zkay.transaction.interface import ZkayHomomorphicCryptoInterface

class ElgamalCrypto(ZkayHomomorphicCryptoInterface):
    params = CryptoParams('paillier')

    # TODO implement anaologously as ecdh_chaskey.py (use bouncycastle in Java to perform BabyJubJub curve operations)
    pass
