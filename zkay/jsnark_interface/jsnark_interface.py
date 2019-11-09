import os
from typing import List

import jnius_config

import zkay.config as cfg
from zkay.zkay_ast.ast import indent

dir_path = os.path.dirname(os.path.realpath(__file__))
jnius_config.add_classpath(os.path.join(dir_path, 'JsnarkCircuitBuilder.jar'))

from jnius import autoclass

jBigint = autoclass('java.math.BigInteger')
jCompiler = autoclass('zkay.ZkayCompiler')


def compile_circuit(circuit_dir: str, javacode: str):
    cwd = os.getcwd()
    os.chdir(circuit_dir)

    jfile = os.path.join(circuit_dir, cfg.jsnark_circuit_classname + ".java")
    with open(jfile, 'w') as f:
        f.write(javacode)
    jCompiler.compile(jfile)

    circuit = jCompiler.load(circuit_dir, cfg.jsnark_circuit_classname)
    circuit.compileCircuit()
    os.chdir(cwd)


def prepare_proof(circuit_dir: str, serialized_args: List[int]):
    cwd = os.getcwd()
    os.chdir(circuit_dir)
    circuit = jCompiler.load(circuit_dir, cfg.jsnark_circuit_classname)
    circuit.prepareProof([jBigint(str(arg), 10) for arg in serialized_args])
    os.chdir(cwd)


_class_template_str = '''\
import java.math.BigInteger;
import circuit.structure.Wire;
import zkay.ZkayCircuitBase;
import zkay.ConditionalAssignmentGadget;

public class {circuit_class_name} extends ZkayCircuitBase {{
    public {circuit_class_name}() {{
        super("{circuit_name}", {rsa_key_bits}, {priv_size}, {pub_size});
    }}

    @Override
    protected void buildCircuit() {{
{init_inputs}

{constraints}
        verifyInputHash();
    }}
}}
'''


def get_jsnark_circuit_class_str(name: str, priv_size: int, pub_size: int, input_init: List[str], constraints: List[str]):
    return _class_template_str.format(circuit_class_name=cfg.jsnark_circuit_classname, circuit_name=name, rsa_key_bits=cfg.rsa_key_bits, priv_size=priv_size, pub_size=pub_size,
                                      init_inputs=indent(indent('\n'.join(input_init))), constraints=indent(indent('\n'.join(constraints))))
