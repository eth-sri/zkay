from abc import ABCMeta, abstractmethod
from typing import List

from compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from compiler.privacy.circuit_generation.proving_scheme import ProvingScheme, VerifyingKey


class CircuitGenerator(metaclass=ABCMeta):
    def __init__(self, circuits: List[CircuitHelper], proving_scheme: ProvingScheme):
        self.circuits = circuits
        self.proving_scheme = proving_scheme

    def generate_circuits(self):
        # Generate code which is needed to issue a transaction for this function (offchain computations)
        self._generate_offchain_code()

        # Generate proof circuit, keys and verification contract
        self._generate_zkcircuit()
        self._generate_keys()

        vk = self._parse_verification_key()
        vcontract_str = self.proving_scheme.generate_verification_contract(vk, 0)

    def _generate_offchain_code(self):
        # Generate python code corresponding to the off-chain computations for the circuit
        pass

    @abstractmethod
    def _parse_verification_key(self) -> VerifyingKey:
        pass

    @abstractmethod
    def _generate_zkcircuit(self):
        pass

    @abstractmethod
    def _generate_keys(self):
        pass