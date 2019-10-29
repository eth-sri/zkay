import os
from abc import ABCMeta, abstractmethod
from typing import List

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.circuit_generation.offchain_compiler import PythonOffchainVisitor
from zkay.compiler.privacy.proving_schemes.proving_scheme import ProvingScheme, VerifyingKey
from zkay.utils.progress_printer import print_step
from zkay.zkay_ast.ast import AST


class CircuitGenerator(metaclass=ABCMeta):
    def __init__(self, transformed_ast: AST, circuits: List[CircuitHelper], proving_scheme: ProvingScheme, output_dir: str):
        self.python_visitor = PythonOffchainVisitor(circuits)
        self.sol_ast = transformed_ast
        self.circuits_to_prove = [c for c in circuits if c.requires_verification()]
        self.proving_scheme = proving_scheme
        self.output_dir = output_dir

    def generate_circuits(self, *, import_keys: bool):
        """
        Generate circuit code and verification contracts based on the provided circuits and proving scheme
        :param import_keys: if false, new verification and prover keys will be generated, otherwise key files for all verifiers
                            are expected to be already present in the respective output directories
        """

        # Generate code which is needed to issue a transaction for this function (offchain computations)
        ocode = self._generate_offchain_code()
        with open(os.path.join(self.output_dir, 'contract.py'), 'w') as f:
            f.write(ocode)

        # Generate proof circuit code
        for circuit in self.circuits_to_prove:
            self._generate_zkcircuit(circuit)

        c_count = len(self.circuits_to_prove)
        for idx, circuit in enumerate(self.circuits_to_prove):
            # Generate prover and verifier keys and verification contract
            if not import_keys:
                with print_step(f'Compilation and key generation for circuit '
                                f'\'{circuit.verifier_contract_type.code()}\' [{idx + 1}/{c_count}]'):
                    self._generate_keys(circuit)
            vk = self._parse_verification_key(circuit)
            with open(os.path.join(self.output_dir, circuit.verifier_contract_filename), 'w') as f:
                f.write(self.proving_scheme.generate_verification_contract(vk, circuit))

    def get_all_key_paths(self) -> List[str]:
        paths = []
        for circuit in self.circuits_to_prove:
            vk, pk = self._get_vk_and_pk_paths(circuit)
            paths += [vk, pk]
        return paths

    def get_verification_contract_filenames(self) -> List[str]:
        return [os.path.join(self.output_dir, circuit.verifier_contract_filename) for circuit in self.circuits_to_prove]

    def _generate_offchain_code(self):
        """ Generate python code corresponding to the off-chain computations for the circuit """
        return self.python_visitor.visit(self.sol_ast)

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
