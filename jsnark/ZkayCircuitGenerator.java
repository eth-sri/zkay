package examples.gadgets.zkay;

import circuit.eval.CircuitEvaluator;
import circuit.structure.CircuitGenerator;
import circuit.structure.Wire;

import java.util.Dictionary;
import java.util.List;

public class ZkayCircuitGenerator extends CircuitGenerator {
	public abstract static class Constraint { }
	public static class EqConstraint extends Constraint {
		private String lhs;
		private String rhs;
	}
	public static class EncConstraint extends Constraint {
		private String plain;
		private String pk;
		private String rnd;
		private String cipher;
	}
	public static class ExprToLocAssignment extends Constraint {
		private String lhs;
	}

	public static class CircuitInput {
		private String name;
		private boolean is_private;
		private int num_elements;
	}

	private Dictionary<String, Wire[]> uint_inputs;
	private Dictionary<String, Wire[]> temp_values;

	private List<CircuitInput> c_inputs;
	private List<Constraint> c_constraints;
	private boolean c_should_hash;

	public ZkayCircuitGenerator(String circuitName, List<CircuitInput> inputs, List<Constraint> constraints, boolean should_hash) {
		super(circuitName);
		this.c_inputs = inputs;
		this.c_constraints = constraints;
		this.c_should_hash = should_hash;
	}

	@Override
	protected void buildCircuit() {
		for (CircuitInput input : c_inputs) {
			if (input.is_private || c_should_hash) {
				uint_inputs.put(input.name, createProverWitnessWireArray(input.num_elements, input.name));
			} else {
				uint_inputs.put(input.name, createInputWireArray(input.num_elements, input.name));
			}
		}

		for (Constraint c : c_constraints) {
			if (c instanceof EqConstraint) {

			} else if (c instanceof EncConstraint) {

			} else {
				if (! (c instanceof ExprToLocAssignment)) throw new IllegalArgumentException();
			}
		}

		if (c_should_hash) {
			// TODO concat all wires
			Wire[] all_pub_inputs = new Wire[0];
			makeOutputArray(new SHA256Uint256ArrayGadget(all_pub_inputs).getOutputWires(), "digest");
		} else {
			makeOutput(oneWire);
		}
	}

	@Override
	public void generateSampleInput(CircuitEvaluator evaluator) {
		/*for (int i = 0; i < num_public_args; i++) {
			evaluator.setWireValue(inputWires[i], i + 1);
		}*/
	}

	public static void main(String[] args) throws Exception {
		/* TODO use pyjnius to invoke generator
		ZkayCircuitGenerator generator = new ZkayCircuitGenerator("sha_256_uintarray");
		generator.generateCircuit();
		generator.evalCircuit();
		System.out.println("Digest = 0x" + Util.padZeros(generator.getCircuitEvaluator().getWireValue(generator.getOutWires().get(0)).toString(16), 32));
		generator.prepFiles();
		generator.runLibsnark(); */
	}
}
