package examples.gadgets.zkay;

import circuit.eval.CircuitEvaluator;
import circuit.structure.CircuitGenerator;
import circuit.structure.Wire;
import util.Util;

public class UintArrayHashGenerator extends CircuitGenerator {
	private static int num_public_args = 2;

	private Wire[] inputWires;

	public UintArrayHashGenerator(String circuitName) {
		super(circuitName);
	}

	@Override
	protected void buildCircuit() {
		// Compute sha256
		inputWires = createProverWitnessWireArray(num_public_args, "secret_input");
		makeOutputArray(new SHA256Uint256ArrayGadget(inputWires).getOutputWires(), "digest");
	}

	@Override
	public void generateSampleInput(CircuitEvaluator evaluator) {
		for (int i = 0; i < num_public_args; i++) {
			evaluator.setWireValue(inputWires[i], i + 1);
		}
	}

	public static void main(String[] args) throws Exception {
		UintArrayHashGenerator generator = new UintArrayHashGenerator("sha_256_uintarray");
		generator.generateCircuit();
		generator.evalCircuit();
		System.out.println("Digest = 0x" + Util.padZeros(generator.getCircuitEvaluator().getWireValue(generator.getOutWires().get(0)).toString(16), 32));
		generator.prepFiles();
		generator.runLibsnark();
	}
}
