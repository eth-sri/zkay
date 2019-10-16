from abc import ABCMeta, abstractmethod

from compiler.privacy.circuit_generation.circuit_helper import ArrayBasedNameFactory
from compiler.privacy.circuit_generation.circuit_helper import CircuitHelper


class G1Point:
    def __init__(self, x: str, y: str):
        self.x: str = x
        self.y: str = y

    def __str__(self):
        return f'{self.x}, {self.y}'


class G2Point:
    def __init__(self, x1: str, x2: str, y1: str, y2: str):
        self.x = [x1, x2]
        self.y = [y1, y2]

    def __str__(self):
        return f'[{self.x[0]}, {self.x[1]}], [{self.y[0]}, {self.y[1]}]'


class VerifyingKey:
    pass


class Proof:
    pass


class ProvingScheme(metaclass=ABCMeta):
    @staticmethod
    def _get_uint_param(name_factory: ArrayBasedNameFactory) -> str:
        if name_factory.count == 0:
            return ''
        else:
            return f', uint[{name_factory.count}] memory {name_factory.base_name}'

    @abstractmethod
    def generate_verification_contract(self, verification_key: VerifyingKey, circuit: CircuitHelper) -> str:
        return ''
