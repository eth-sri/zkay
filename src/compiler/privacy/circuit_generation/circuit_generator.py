import os
from abc import ABCMeta, abstractmethod
from typing import List

from compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from compiler.privacy.circuit_generation.proving_scheme import ProvingScheme, VerifyingKey
from zkay_ast.ast import AST


class CircuitGenerator(metaclass=ABCMeta):
    def __init__(self, ast: AST, circuits: List[CircuitHelper], proving_scheme: ProvingScheme, output_dir: str):
        self.ast = ast
        self.circuits = [c for c in circuits if c.requires_verification()]
        self.proving_scheme = proving_scheme
        self.output_dir = output_dir

    def generate_circuits(self):
        # Generate code which is needed to issue a transaction for this function (offchain computations)
        self._generate_offchain_code()

        for circuit in self.circuits:
            # Generate proof circuit, keys and verification contract
            self._generate_zkcircuit()
            self._generate_keys()

            vk = self._parse_verification_key()
            with open(os.path.join(self.output_dir, circuit.verifier_contract.filename), 'w') as f:
                f.write(self.proving_scheme.generate_verification_contract(vk, circuit))

    def _generate_offchain_code(self):
        # Generate python code corresponding to the off-chain computations for the circuit
        pass

    #@abstractmethod
    def _parse_verification_key(self) -> VerifyingKey:
        return self.proving_scheme.dummy_vk()

    #@abstractmethod
    def _generate_zkcircuit(self):
        pass

    #@abstractmethod
    def _generate_keys(self):
        pass