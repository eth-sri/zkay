import functools
import os
from abc import ABCMeta, abstractmethod
from multiprocessing import Pool, Value
from typing import List, Tuple

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.proving_scheme.proving_scheme import ProvingScheme, VerifyingKey
from zkay.config import cfg, zk_print
from zkay.utils.progress_printer import print_step
from zkay.utils.timer import time_measure


class CircuitGenerator(metaclass=ABCMeta):
    """
    A circuit generator takes an abstract circuit representation and turns it into a concrete zk-snark circuit.

    It also handles prover/verification key generation and parsing, and generates the verification contracts using the supplied
    proving scheme.
    """

    def __init__(self, circuits: List[CircuitHelper], proving_scheme: ProvingScheme, output_dir: str, parallel_keygen: bool):
        """
        Create a circuit generator instance

        :param circuits: list which contains the corresponding circuit helper for every function in the contract which requires verification
        :param proving_scheme: the proving scheme instance to be used for verification contract generation
        :param output_dir: base directory where the zkay compilation output is located
        :param parallel_keygen: if true, multiple python processes are used to generate keys in parallel
        """

        self.circuits = {circ.fct: circ for circ in circuits}
        self.circuits_to_prove = [c for c in circuits if c.requires_verification() and c.fct.can_be_external]
        self.proving_scheme = proving_scheme
        self.output_dir = output_dir
        self.parallel_keygen = parallel_keygen
        self.p_count = min(os.cpu_count(), len(self.circuits_to_prove))

    def generate_circuits(self, *, import_keys: bool):
        """
        Generate circuit code and verification contracts based on the provided circuits and proving scheme.

        :param import_keys: if false, new verification and prover keys will be generated, otherwise key files for all verifiers
                            are expected to be already present in the respective output directories
        """
        # Generate proof circuit code

        # Compile circuits
        c_count = len(self.circuits_to_prove)
        zk_print(f'Compiling {c_count} circuits...')

        gen_circs = functools.partial(self._generate_zkcircuit, import_keys)
        with time_measure('circuit_compilation', True):
            if cfg.is_unit_test:
                modified = list(map(gen_circs, self.circuits_to_prove))
            else:
                with Pool(processes=self.p_count) as pool:
                    modified = pool.map(gen_circs, self.circuits_to_prove)

        if import_keys:
            for path in self.get_all_key_paths():
                if not os.path.exists(path):
                    raise RuntimeError("Zkay contract import failed: Missing keys")
        else:
            modified_circuits_to_prove = [circ for t, circ in zip(modified, self.circuits_to_prove)
                                          if t or not all(map(os.path.exists, self._get_vk_and_pk_paths(circ)))]

            # Generate keys in parallel
            zk_print(f'Generating keys for {c_count} circuits...')
            with time_measure('key_generation', True):
                if self.parallel_keygen and not cfg.is_unit_test:
                    counter = Value('i', 0)
                    with Pool(processes=self.p_count, initializer=self.__init_worker, initargs=(counter, c_count,)) as pool:
                        pool.map(self._generate_keys_par, modified_circuits_to_prove)
                else:
                    for circ in modified_circuits_to_prove:
                        self._generate_keys(circ)

        with print_step('Write verification contracts'):
            for circuit in self.circuits_to_prove:
                vk = self._parse_verification_key(circuit)
                pk_hash = self._get_prover_key_hash(circuit)
                with open(os.path.join(self.output_dir, circuit.verifier_contract_filename), 'w') as f:
                    primary_inputs = self._get_primary_inputs(circuit)
                    f.write(self.proving_scheme.generate_verification_contract(vk, circuit, primary_inputs, pk_hash))

    def get_all_key_paths(self) -> List[str]:
        """Return paths of all key files for this contract."""
        paths = []
        for circuit in self.circuits_to_prove:
            vk, pk = self._get_vk_and_pk_paths(circuit)
            paths += [vk, pk]
        return paths

    def get_verification_contract_filenames(self) -> List[str]:
        """Return file paths for all verification contracts generated by this CircuitGenerator"""
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
            zk_print(f'Generated keys for circuit '
                  f'\'{circuit.verifier_contract_type.code()}\' [{finish_counter.value}/{c_count}]')

    def _get_circuit_output_dir(self, circuit: CircuitHelper):
        """Return the output directory for an individual circuit"""
        return os.path.join(self.output_dir, cfg.get_circuit_output_dir_name(circuit.get_verification_contract_name()))

    def _get_vk_and_pk_paths(self, circuit: CircuitHelper) -> Tuple[str, ...]:
        """Return a tuple which contains the paths to the verification and prover key files."""
        output_dir = self._get_circuit_output_dir(circuit)
        return tuple(os.path.join(output_dir, fname) for fname in self.get_vk_and_pk_filenames())

    @abstractmethod
    def _generate_zkcircuit(self, import_keys: bool, circuit: CircuitHelper) -> bool:
        """
        Generate code and compile a single circuit.

        When implementing a new backend, this function should generate a concrete circuit representation, which has:
        a) circuit IO corresponding to circuit.sec_idfs/output_idfs/input_idfs
        b) logic corresponding to the non-CircCall statements in circuit.phi
        c) a), b) and c) for the circuit associated with the target function for every CircCall statement in circuit.phi

        The output of this function should be in a state where key generation can be invoked immediately without further transformations
        (i.e. any intermediary compilation steps should also happen here).

        It should be stored in self._get_circuit_output_dir(circuit)

        :return: True if the circuit was modified since last generation (need to generate new keys)
        """
        pass

    @abstractmethod
    def _generate_keys(self, circuit: CircuitHelper):
        """Generate prover and verification keys for the circuit stored in self._get_circuit_output_dir(circuit)."""
        pass

    @classmethod
    @abstractmethod
    def get_vk_and_pk_filenames(cls) -> Tuple[str, ...]:
        pass

    @abstractmethod
    def _parse_verification_key(self, circuit: CircuitHelper) -> VerifyingKey:
        """Parse the generated verificaton key file and return a verification key object compatible with self.proving_scheme"""
        return self.proving_scheme.dummy_vk()

    @abstractmethod
    def _get_prover_key_hash(self, circuit: CircuitHelper) -> bytes:
        pass

    def _get_primary_inputs(self, circuit: CircuitHelper) -> List[str]:
        """
        Return list of all public input locations
        :param circuit: abstract circuit representation
        :return: list of location strings, a location is either an identifier name or an array index
        """

        inputs = circuit.public_arg_arrays

        if cfg.should_use_hash(circuit):
            return [self.proving_scheme.hash_var_name]
        else:
            primary_inputs = []
            for name, count in inputs:
                primary_inputs += [f'{name}[{i}]' for i in range(count)]
            return primary_inputs
