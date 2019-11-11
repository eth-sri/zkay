import os
from abc import ABCMeta, abstractmethod
from multiprocessing import Pool, Value
from typing import List

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.circuit_generation.offchain_compiler import PythonOffchainVisitor
from zkay.config import should_use_hash
from zkay.compiler.privacy.proving_schemes.proving_scheme import ProvingScheme, VerifyingKey
from zkay.utils.progress_printer import print_step
from zkay.utils.timer import time_measure
from zkay.zkay_ast.ast import AST


class CircuitGenerator(metaclass=ABCMeta):
    def __init__(self, transformed_ast: AST, circuits: List[CircuitHelper], proving_scheme: ProvingScheme, output_dir: str, parallel_keygen: bool):
        self.python_visitor = PythonOffchainVisitor(circuits)
        self.sol_ast = transformed_ast
        self.circuits_to_prove = [c for c in circuits if c.requires_verification()]
        self.proving_scheme = proving_scheme
        self.output_dir = output_dir
        self.parallel_keygen = parallel_keygen
        self.p_count = min(os.cpu_count(), len(self.circuits_to_prove))

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
        c_count = len(self.circuits_to_prove)
        print(f'Compiling {c_count} circuits...')
        with time_measure('circuit_compilation', True):
            with Pool(processes=self.p_count) as pool:
                pool.map(self._generate_zkcircuit, self.circuits_to_prove)

        if import_keys:
            # Import TODO
            pass
        else:
            # Generate keys in parallel
            print(f'Generating keys for {c_count} circuits...')
            with time_measure('key_generation', True):
                counter = Value('i', 0)
                if self.parallel_keygen:
                    with Pool(processes=self.p_count, initializer=self.__init_worker, initargs=(counter, c_count,)) as pool:
                        pool.map(self._generate_keys_par, self.circuits_to_prove)
                else:
                    for circ in self.circuits_to_prove:
                        self._generate_keys(circ)

        with print_step('Write verification contracts'):
            for circuit in self.circuits_to_prove:
                vk = self._parse_verification_key(circuit)
                with open(os.path.join(self.output_dir, circuit.verifier_contract_filename), 'w') as f:
                    should_hash = should_use_hash(circuit.num_public_args)
                    primary_inputs = self._get_primary_inputs(should_hash, circuit)
                    f.write(self.proving_scheme.generate_verification_contract(vk, circuit, should_hash, primary_inputs))

    def get_all_key_paths(self) -> List[str]:
        paths = []
        for circuit in self.circuits_to_prove:
            vk, pk = self._get_vk_and_pk_paths(circuit)
            paths += [vk, pk]
        return paths

    def get_verification_contract_filenames(self) -> List[str]:
        return [os.path.join(self.output_dir, circuit.verifier_contract_filename) for circuit in self.circuits_to_prove]

    @staticmethod
    def __init_worker(counter, total_count):
        global finish_counter
        global c_count

        finish_counter = counter
        c_count = total_count

    def _generate_keys_par(self, circuit: CircuitHelper):
        self._generate_keys(circuit)
        with finish_counter.get_lock():
            finish_counter.value += 1
            print(f'Generated keys for circuit '
                  f'\'{circuit.verifier_contract_type.code()}\' [{finish_counter.value}/{c_count}]')

    def _generate_offchain_code(self):
        """ Generate python code corresponding to the off-chain computations for the circuit """
        return self.python_visitor.visit(self.sol_ast)

    def _get_circuit_output_dir(self, circuit: CircuitHelper):
        return os.path.join(self.output_dir, f'{circuit.get_circuit_name()}_out')

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

    def _get_primary_inputs(self, should_hash: bool, circuit: CircuitHelper) -> List[str]:
        inputs = circuit.public_arg_arrays

        if should_hash:
            return [self.proving_scheme.hash_var_name]
        else:
            primary_inputs = []
            for name, count in inputs:
                primary_inputs += [f'{name}[{i}]' for i in range(count)]
            return primary_inputs
