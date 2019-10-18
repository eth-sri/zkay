import os
from abc import ABCMeta, abstractmethod
from typing import List

from compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from compiler.privacy.proving_schemes.proving_scheme import ProvingScheme, VerifyingKey
from utils.progress_printer import print_step
from zkay_ast.ast import AST


class CircuitGenerator(metaclass=ABCMeta):
    def __init__(self, ast: AST, circuits: List[CircuitHelper], proving_scheme: ProvingScheme, output_dir: str):
        self.ast = ast
        self.circuits = [c for c in circuits if c.requires_verification()]
        self.proving_scheme = proving_scheme
        self.output_dir = output_dir

    def generate_circuits(self, *, import_keys: bool):
        """
        Generate circuit code and verification contracts based on the provided circuits and proving scheme
        :param import_keys: if false, new verification and prover keys will be generated, otherwise key files for all verifiers
                            are expected to be already present in the respective output directories
        """

        # Generate code which is needed to issue a transaction for this function (offchain computations)
        self._generate_offchain_code()

        # Generate proof circuit code
        for circuit in self.circuits:
            self._generate_zkcircuit(circuit)

        c_count = len(self.circuits)
        for idx, circuit in enumerate(self.circuits):
            # Generate prover and verifier keys and verification contract
            if not import_keys:
                with print_step(f'Compilation and key generation for circuit \'{circuit.verifier_contract.contract_type.type_name.names[0]}\' [{idx+1}/{c_count}]'):
                    self._generate_keys(circuit)
            vk = self._parse_verification_key(circuit)
            with open(os.path.join(self.output_dir, circuit.verifier_contract.filename), 'w') as f:
                f.write(self.proving_scheme.generate_verification_contract(vk, circuit))

    def get_all_key_paths(self) -> List[str]:
        paths = []
        for circuit in self.circuits:
            vk, pk = self._get_vk_and_pk_paths(circuit)
            paths += [vk, pk]
        return paths

    def get_verification_contract_filenames(self) -> List[str]:
        return [os.path.join(self.output_dir, circuit.verifier_contract.filename) for circuit in self.circuits]

    def _generate_offchain_code(self):
        # Generate python code corresponding to the off-chain computations for the circuit
        pass

    @abstractmethod
    def _generate_zkcircuit(self, circuit: CircuitHelper):
        pass

    @abstractmethod
    def _generate_keys(self, circuit: CircuitHelper):
        pass

    @abstractmethod
    def _get_vk_and_pk_paths(self, circuit: CircuitHelper):
        pass

    @abstractmethod
    def _parse_verification_key(self, circuit: CircuitHelper) -> VerifyingKey:
        return self.proving_scheme.dummy_vk()
