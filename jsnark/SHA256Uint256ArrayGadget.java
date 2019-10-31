package examples.gadgets.zkay;

import circuit.structure.Wire;
import circuit.structure.WireArray;
import examples.gadgets.hash.SHA256Gadget;

public class SHA256Uint256ArrayGadget extends SHA256Gadget {
    private static int bytes_per_word = 32;
    private static int out_len = 1;

    private static Wire[] uint_output;

    private static Wire[] convert_inputs_to_bytes(Wire[] uint256_inputs) {
        Wire[] input_bytes = new WireArray(uint256_inputs).getBits(bytes_per_word * 8).packBitsIntoWords(8);
        // Reverse byte order because jsnark reverses internally when packing
        for (int j = 0; j < uint256_inputs.length; ++j) {
            for (int i = 0; i < bytes_per_word / 2; ++i) {
                Wire tmp = input_bytes[j * bytes_per_word + i];
                input_bytes[j * bytes_per_word + i] = input_bytes[(j + 1) * bytes_per_word - 1 - i];
                input_bytes[(j + 1) * bytes_per_word - 1 - i] = tmp;
            }
        }
        return input_bytes;
    }

    public SHA256Uint256ArrayGadget(Wire[] uint256_inputs, String... desc) {
        super(convert_inputs_to_bytes(uint256_inputs), 8, uint256_inputs.length * bytes_per_word, false, true, desc);
    }

    @Override
    protected void buildCircuit() {
        super.buildCircuit();
        Wire[] digest = super.getOutputWires();
        // Move words around again because jsnark changes word order when packing
        if (out_len == 1) {
            for (int i = 0; i < 4 / out_len; ++i) {
                Wire tmp = digest[i];
                digest[i] = digest[7 - i];
                digest[7 - i] = tmp;
            }
        } else {
            if (out_len != 2) throw new IllegalArgumentException();
            for (int j = 0; j < 2; ++j) {
                for (int i = 0; i < 2; ++i) {
                    Wire tmp = digest[4 * j + i];
                    digest[4 * j + i] = digest[4 * j + 3 - i];
                    digest[4 * j + 3 - i] = tmp;
                }
            }
        }
        uint_output = new WireArray(digest).packWordsIntoLargerWords(32, 8 / out_len);
        if (uint_output.length != out_len) throw new RuntimeException("Wrong wire length");
    }

    @Override
    public Wire[] getOutputWires() {
        return uint_output;
    }
}
