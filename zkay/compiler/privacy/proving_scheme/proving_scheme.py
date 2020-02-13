from abc import ABCMeta, abstractmethod
from typing import List

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper


class G1Point:
    """Data class to represent curve points"""

    def __init__(self, x: str, y: str):
        """Construct G1Point from coordinate integer literal strings."""
        self.x: str = x
        self.y: str = y

    @staticmethod
    def from_seq(seq):
        """
        Construct G1Point from a sequence of length 2 of integer literal strings
        First entry makes up the X coordinate, second entry makes up the Y coordinate
        """
        assert len(seq) == 2
        return G1Point(seq[0], seq[1])

    def __str__(self):
        return f'uint256({self.x}), uint256({self.y})'


class G2Point:
    """Data class to represent curve points which are encoded using two field elements"""

    def __init__(self, x1: str, x2: str, y1: str, y2: str):
        self.x = (x1, x2)
        self.y = (y1, y2)

    @staticmethod
    def from_seq(seq):
        """
        Construct G1Point from a sequence of length 4 of integer literal strings
        First two entries make up the X coordinate, last two entries make up the Y coordinate
        """
        assert len(seq) == 4
        return G2Point(seq[0], seq[1], seq[2], seq[3])

    def __str__(self):
        return f'[uint256({self.x[0]}), uint256({self.x[1]})], [uint256({self.y[0]}), uint256({self.y[1]})]'


class VerifyingKey:
    """Abstract base data class for verification keys"""
    pass


class Proof:
    """Abstract base data class for proofs"""
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

    def dummy_vk(self) -> VerifyingKey:
        """
        Return a dummy verification key with all the necessary fields (for testing).
        """
        pass
