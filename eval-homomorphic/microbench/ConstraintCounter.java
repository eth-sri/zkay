import circuit.eval.CircuitEvaluator;
import circuit.structure.CircuitGenerator;
import circuit.structure.Wire;
import circuit.structure.WireArray;
import zkay.*;

import java.math.BigInteger;

public class ConstraintCounter {
    private static class EncCircuitGen extends CircuitGenerator {
        public EncCircuitGen() {
            super("Encryption");
        }

        @Override
        protected void buildCircuit() {
            Wire rand = createInputWire();
            Wire[] rand_bits = rand.getBitWires(256).asArray();
            Wire msg = createInputWire();
            Wire[] msg_bits = msg.getBitWires(32).asArray();
            Wire pk_x = createInputWire();
            Wire pk_y = createInputWire();
            ZkayElgamalEncGadget gadget = new ZkayElgamalEncGadget(msg_bits, new ZkayBabyJubJubGadget.JubJubPoint(pk_x, pk_y), rand_bits);
            makeOutputArray(gadget.getOutputWires(), "cipher");
        }

        @Override
        public void generateSampleInput(CircuitEvaluator evaluator) { }
    }

    private static class DecCircuitGen extends CircuitGenerator {
        public DecCircuitGen() {
            super("Decryption");
        }

        @Override
        protected void buildCircuit() {
            Wire pk_x = createInputWire();
            Wire pk_y = createInputWire();
            Wire sk = createInputWire();
            Wire[] sk_bits = sk.getBitWires(256).asArray();
            Wire c1_x = createInputWire();
            Wire c1_y = createInputWire();
            Wire c2_x = createInputWire();
            Wire c2_y = createInputWire();
            Wire msg = createInputWire();

            ZkayElgamalDecGadget gadget = new ZkayElgamalDecGadget(new ZkayBabyJubJubGadget.JubJubPoint(pk_x, pk_y), sk_bits, new ZkayBabyJubJubGadget.JubJubPoint(c1_x, c1_y), new ZkayBabyJubJubGadget.JubJubPoint(c2_x, c2_y), msg);
            makeOutputArray(gadget.getOutputWires(), "cipher");
        }

        @Override
        public void generateSampleInput(CircuitEvaluator evaluator) { }
    }

    private static class AddCircuitGen extends CircuitGenerator {
        public AddCircuitGen() {
            super("Addition");
        }

        @Override
        protected void buildCircuit() {
            Wire c1_x = createInputWire();
            Wire c1_y = createInputWire();
            Wire c2_x = createInputWire();
            Wire c2_y = createInputWire();
            Wire d1_x = createInputWire();
            Wire d1_y = createInputWire();
            Wire d2_x = createInputWire();
            Wire d2_y = createInputWire();
            ZkayElgamalAddGadget gadget = new ZkayElgamalAddGadget(new ZkayBabyJubJubGadget.JubJubPoint(c1_x, c1_y), new ZkayBabyJubJubGadget.JubJubPoint(c2_x, c2_y), new ZkayBabyJubJubGadget.JubJubPoint(d1_x, d1_y), new ZkayBabyJubJubGadget.JubJubPoint(d2_x, d2_y));
            makeOutputArray(gadget.getOutputWires(), "cipher");
        }

        @Override
        public void generateSampleInput(CircuitEvaluator evaluator) { }
    }

    private static class MulCircuitGen extends CircuitGenerator {
        public MulCircuitGen() {
            super("Multiplication");
        }

        @Override
        protected void buildCircuit() {
            Wire c1_x = createInputWire();
            Wire c1_y = createInputWire();
            Wire c2_x = createInputWire();
            Wire c2_y = createInputWire();
            Wire scalar = createInputWire();
            Wire[] scalar_bits = scalar.getBitWires(32).asArray();
            ZkayElgamalMulGadget gadget = new ZkayElgamalMulGadget(new ZkayBabyJubJubGadget.JubJubPoint(c1_x, c1_y), new ZkayBabyJubJubGadget.JubJubPoint(c2_x, c2_y), scalar_bits);
            makeOutputArray(gadget.getOutputWires(), "cipher");
        }

        @Override
        public void generateSampleInput(CircuitEvaluator evaluator) { }
    }

    private static class RerandCircuitGen extends CircuitGenerator {
        public RerandCircuitGen() {
            super("Rerandomize");
        }

        @Override
        protected void buildCircuit() {
            Wire c1_x = createInputWire();
            Wire c1_y = createInputWire();
            Wire c2_x = createInputWire();
            Wire c2_y = createInputWire();
            Wire pk_x = createInputWire();
            Wire pk_y = createInputWire();
            Wire rand = createInputWire();
            Wire[] rand_bits = rand.getBitWires(256).asArray();
            ZkayElgamalRerandGadget gadget = new ZkayElgamalRerandGadget(new ZkayBabyJubJubGadget.JubJubPoint(c1_x, c1_y), new ZkayBabyJubJubGadget.JubJubPoint(c2_x, c2_y), new ZkayBabyJubJubGadget.JubJubPoint(pk_x, pk_y), rand_bits);
            makeOutputArray(gadget.getOutputWires(), "cipher");
        }

        @Override
        public void generateSampleInput(CircuitEvaluator evaluator) { }
    }

    public static void main(String[] args) {
        EncCircuitGen cgen = new EncCircuitGen();
        cgen.generateCircuit();
        DecCircuitGen dgen = new DecCircuitGen();
        dgen.generateCircuit();
        AddCircuitGen agen = new AddCircuitGen();
        agen.generateCircuit();
        MulCircuitGen mgen = new MulCircuitGen();
        mgen.generateCircuit();
        RerandCircuitGen rgen = new RerandCircuitGen();
        rgen.generateCircuit();
    }
}
