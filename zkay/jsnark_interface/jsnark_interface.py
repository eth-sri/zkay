import os

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.library_contracts import should_use_hash

import jnius_config
dir_path = os.path.dirname(os.path.realpath(__file__))
jnius_config.add_classpath(os.path.join(dir_path, 'JsnarkCircuitBuilder.jar'))

from jnius import PythonJavaClass, java_method, autoclass

jBigint = autoclass('java.math.BigInteger')
jMap = autoclass('java.util.Map')
jWire = autoclass('circuit.structure.Wire')
jCircuitGenerator = autoclass('circuit.structure.CircuitGenerator')
jZkayCircuitGenerator = autoclass('zkay.ZkayCircuitGenerator')
jCircuitInput = autoclass('zkay.ZkayCircuitGenerator$CircuitInput')
jEncGadget = autoclass('zkay.DummyEncryptionGadget')
jCondAssignmentGadget = autoclass('zkay.ConditionalAssignmentGadget')


class PythonJsnarkConstraintGenerator(PythonJavaClass):
    __javainterfaces__ = ['zkay/ZkayJsnarkInterface']

    def __init__(self):
        super(PythonJsnarkConstraintGenerator, self).__init__()
        self.jsnark_visitor = None

    @java_method('(Lcircuit/structure/CircuitGenerator;Ljava/util/Map;)V')
    def add_circuit_constraints(self, generator: jCircuitGenerator, uint_inputs: jMap):
        inputs = {}
        keys = uint_inputs.keySet().toArray()
        for i in keys:
            inputs[i] = uint_inputs.get(i)
        self.jsnark_visitor.visitCircuit(generator, inputs)


def run_jsnark(jsnark_visitor, circuit: CircuitHelper, output_dir: str):
    cg = PythonJsnarkConstraintGenerator()
    cg.jsnark_visitor = jsnark_visitor

    priv_list = []
    for priv in circuit.s:
        priv_list.append(jCircuitInput(priv.name, 1))

    pub_list = []
    if circuit.in_name_factory.count > 0:
        pub_list.append(jCircuitInput(circuit.in_base_name, circuit.in_name_factory.count))
    if circuit.out_name_factory.count > 0:
        pub_list.append(jCircuitInput(circuit.out_base_name, circuit.out_name_factory.count))

    should_hash = should_use_hash(circuit.in_name_factory.count + circuit.out_name_factory.count)

    cwd = os.getcwd()
    os.chdir(output_dir)
    zkay_gen = jZkayCircuitGenerator(circuit.get_circuit_name(), should_hash, cg, priv_list, pub_list)
    zkay_gen.generateCircuit()
    zkay_gen.evalCircuit()
    zkay_gen.prepFiles()
    os.chdir(cwd)
