from abc import ABCMeta, abstractmethod
from typing import List

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper


class G1Point:
    def __init__(self, x: str, y: str):
        self.x: str = x
        self.y: str = y

    @staticmethod
    def from_seq(seq):
        assert len(seq) == 2
        return G1Point(seq[0], seq[1])

    def __str__(self):
        return f'uint256({self.x}), uint256({self.y})'


class G2Point:
    def __init__(self, x1: str, x2: str, y1: str, y2: str):
        self.x = (x1, x2)
        self.y = (y1, y2)

    @staticmethod
    def from_seq(seq):
        assert len(seq) == 4
        return G2Point(seq[0], seq[1], seq[2], seq[3])

    def __str__(self):
        return f'[uint256({self.x[0]}), uint256({self.x[1]})], [uint256({self.y[0]}), uint256({self.y[1]})]'


class VerifyingKey:
    pass


class Proof:
    pass


class ProvingScheme(metaclass=ABCMeta):
    verify_libs_contract_filename = "./verify_libs.sol"
    snark_scalar_field_var_name = 'snark_scalar_field'
    hash_var_name = 'hash'
    name = 'none'

    @abstractmethod
    def generate_verification_contract(self, verification_key: VerifyingKey, circuit: CircuitHelper, should_hash: bool, primary_inputs: List[str]) -> str:
        pass

    def dummy_vk(self) -> VerifyingKey:
        pass
