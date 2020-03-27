from abc import ABCMeta, abstractmethod
from typing import List

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper


class G1Point:
    """Data class to represent curve points"""

    def __init__(self, x: str, y: str):
        """Construct G1Point from coordinate integer literal strings."""
        self.x: str = x
        self.y: str = y

    def negated(self):
        q = 21888242871839275222246405745257275088696311157297823662689037894645226208583
        if self.x == '0' and self.y == '0':
            return G1Point('0', '0')
        else:
            return G1Point(self.x, hex(q - (int(self.y, 0) % q)))

    @staticmethod
    def from_seq(seq):
        """
        Construct G1Point from a sequence of length 2 of integer literal strings
        First entry makes up the X coordinate, second entry makes up the Y coordinate
        """
        assert len(seq) == 2
        return G1Point(seq[0], seq[1])

    @staticmethod
    def from_it(it):
        return G1Point(next(it), next(it))

    def __str__(self):
        return f'uint256({self.x}), uint256({self.y})'


class G2Point:
    """Data class to represent curve points which are encoded using two field elements"""

    def __init__(self, x1: str, x2: str, y1: str, y2: str):
        self.x = G1Point(x1, x2) # not really a G1Point, but can reuse __str__
        self.y = G1Point(y1, y2)

    @staticmethod
    def from_seq(seq):
        """
        Construct G1Point from a sequence of length 4 of integer literal strings
        First two entries make up the X coordinate, last two entries make up the Y coordinate
        """
        assert len(seq) == 4
        return G2Point(seq[0], seq[1], seq[2], seq[3])

    @staticmethod
    def from_it(it):
        return G2Point(next(it), next(it), next(it), next(it))

    def __str__(self):
        return f'[{self.x}], [{self.y}]'


class VerifyingKey(metaclass=ABCMeta):
    """Abstract base data class for verification keys"""

    @classmethod
    @abstractmethod
    def create_dummy_key(cls):
        """Generate a dummy key."""
        pass


class ProvingScheme(metaclass=ABCMeta):
    """
    Abstract base class for proving schemes

    A proving scheme provides functionality to generate a verification contract from a proving-scheme dependent verification-key
    and an abstract circuit representation
    """

    verify_libs_contract_filename = "./verify_libs.sol"
    snark_scalar_field_var_name = 'snark_scalar_field'
    hash_var_name = 'hash'
    """Special variable names usable by the verification contract"""

    name = 'none'
    """Proving scheme name, overridden by child classes"""

    class VerifyingKey(VerifyingKey, metaclass=ABCMeta):
        pass

    @abstractmethod
    def generate_verification_contract(self, verification_key: VerifyingKey, circuit: CircuitHelper, primary_inputs: List[str],
                                       prover_key_hash: bytes) -> str:
        """
        Generate a verification contract for the zk-snark corresponding to circuit.

        :param verification_key: parsed verification key which was previously generated for circuit
        :param circuit: the circuit for which to generate the verification contract
        :param primary_inputs: list of all public input locations (strings which represent either identifiers or array index expressions)
        :param prover_key_hash: sha3 hash of the prover key
        :return: verification contract text
        """
        pass
