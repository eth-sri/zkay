import os
from typing import List

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.config import cfg
from zkay.utils.helpers import hash_file
from zkay.utils.run_command import run_command
from zkay.zkay_ast.ast import indent

# path jo jsnark interface jar
circuit_builder_jar = os.path.join(os.path.dirname(os.path.realpath(__file__)),  'JsnarkCircuitBuilder.jar')
circuit_builder_jar_hash = hash_file(circuit_builder_jar).hex()


def compile_circuit(circuit_dir: str, javacode: str):
    """
    Compile the given circuit java code and then compile the circuit which it describes using jsnark.
    :param circuit_dir: output directory
    :param javacode: circuit code (java class which uses the custom jsnark wrapper API)
    :raise SubprocessError: if compilation fails
    """
    jfile = os.path.join(circuit_dir, cfg.jsnark_circuit_classname + ".java")
    with open(jfile, 'w') as f:
        f.write(javacode)

    # Compile the circuit java file
    run_command(['javac', '-cp', f'{circuit_builder_jar}', jfile], cwd=circuit_dir)

    # Run jsnark to generate the circuit
    run_command(['java', '-Xms4096m', '-Xmx16384m', '-cp', f'{circuit_builder_jar}:{circuit_dir}', cfg.jsnark_circuit_classname, 'compile'], cwd=circuit_dir, debug_output_key='jsnark')


def prepare_proof(circuit_dir: str, serialized_args: List[int]):
    """
    Generate a libsnark circuit input file by evaluating the circuit in jsnark using the provided input values.
    :param circuit_dir: directory where the compiled circuit is located
    :param serialized_args: public inputs, public outputs and private inputs in the order in which they are defined in the circuit
    :raise SubprocessError: if circuit evaluation fails
    """
    serialized_arg_str = [format(arg, 'x') for arg in serialized_args]

    # Run jsnark to evaluate the circuit and compute prover inputs
    run_command(['java', '-Xms4096m', '-Xmx16384m', '-cp', f'{circuit_builder_jar}:{circuit_dir}', cfg.jsnark_circuit_classname, 'prove', *serialized_arg_str], cwd=circuit_dir, debug_output_key='jsnark')


_class_template_str = '''\
import zkay.ZkayCircuitBase;
import static zkay.ZkayType.ZkUint;
import static zkay.ZkayType.ZkInt;
import static zkay.ZkayType.ZkBool;

public class {circuit_class_name} extends ZkayCircuitBase {{
    public {circuit_class_name}() {{
        super("{circuit_name}", "{crypto_backend}", {key_bits}, {pub_in_size}, {pub_out_size}, {priv_in_size}, {use_input_hashing});
    }}
{fdefs}
    @Override
    protected void buildCircuit() {{
        super.buildCircuit();
{circuit_statements}
    }}

    public static void main(String[] args) {{
        {circuit_class_name} circuit = new {circuit_class_name}();
        circuit.run(args);
    }}
}}
'''


def get_jsnark_circuit_class_str(circuit: CircuitHelper, fdefs: List[str], circuit_statements: List[str]) -> str:
    """
    Inject circuit and input code into jsnark-wrapper skeleton.

    :param circuit: the abstract circuit to which this java code corresponds
    :param fdefs: java function definition with circuit code for each transitively called function (public calls in this circuit's function)
    :param circuit_statements: the java code corresponding to this circuit
    :return: complete java file as string
    """
    function_definitions = '\n\n'.join(fdefs)
    if function_definitions:
        function_definitions = f'\n{function_definitions}\n'
    return _class_template_str.format(circuit_class_name=cfg.jsnark_circuit_classname, crypto_backend=cfg.crypto_backend,
                                      circuit_name=circuit.get_verification_contract_name(),
                                      key_bits=cfg.key_bits, pub_in_size=circuit.in_size_trans, pub_out_size=circuit.out_size_trans,
                                      priv_in_size=circuit.priv_in_size_trans, use_input_hashing=str(cfg.should_use_hash(circuit)).lower(),
                                      fdefs=indent(function_definitions), circuit_statements=indent(indent('\n'.join(circuit_statements))))
