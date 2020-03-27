"""
This module defines the verification key, proof and verification contract format for the Groth16 proving scheme

See "On the Size of Pairing-based Non-interactive Arguments", Jens Groth, IACR-EUROCRYPT-2016
https://eprint.iacr.org/2016/260
"""

from typing import List

from zkay.config import cfg

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.library_contracts import bn128_scalar_field, bn128_scalar_field_bits
from zkay.compiler.privacy.proving_scheme.proving_scheme import ProvingScheme, G1Point, G2Point, VerifyingKey
from zkay.utils.multiline_formatter import MultiLineFormatter


class ProvingSchemeGroth16(ProvingScheme):
    name = 'groth16'

    class VerifyingKey(VerifyingKey):
        def __init__(self, a: G1Point, b: G2Point, gamma: G2Point, delta: G2Point, gamma_abc: List[G1Point]):
            self.a = a
            self.b = b
            self.gamma = gamma
            self.delta = delta
            self.gamma_abc = gamma_abc

        @classmethod
        def create_dummy_key(cls):
            p1 = G1Point('0', '0')
            p2 = G2Point('0', '0', '0', '0')
            return cls(p1, p2, p2, p2, [p1, p1])

    def generate_verification_contract(self, verification_key: VerifyingKey, circuit: CircuitHelper, primary_inputs: List[str],
                                       prover_key_hash: bytes) -> str:
        vk = verification_key
        should_hash = cfg.should_use_hash(circuit)

        query_length = len(vk.gamma_abc)
        assert query_length == len(primary_inputs) + 1

        assert primary_inputs, "No public inputs"
        first_pi = primary_inputs[0]
        potentially_overflowing_pi = [pi for pi in primary_inputs if pi not in ['1', self.hash_var_name]]

        # Verification contract uses the pairing library from ZoKrates (MIT license)
        # https://github.com/Zokrates/ZoKrates/blob/d8cde9e1c060cc654413f01c8414ea4eaa955d87/zokrates_core/src/proof_system/bn128/utils/solidity.rs#L398
        x = MultiLineFormatter() * f'''\
        pragma solidity {cfg.zkay_solc_version_compatibility};

        import {{ Pairing as P }} from "{ProvingScheme.verify_libs_contract_filename}";

        contract {circuit.get_verification_contract_name()} {{''' / f'''\
            using P for P.G1Point;
            using P for P.G2Point;

            bytes32 public constant {cfg.prover_key_hash_name} = 0x{prover_key_hash.hex()};
            uint256 constant {self.snark_scalar_field_var_name} = {bn128_scalar_field};

            struct Proof {{
                P.G1Point a;
                P.G2Point b;
                P.G1Point c;
            }}

            struct Vk {{
                P.G1Point a_neg;
                P.G2Point b;
                P.G2Point gamma;
                P.G2Point delta;
                P.G1Point[{query_length}] gamma_abc;
            }}

            function getVk() pure internal returns (Vk memory vk) {{''' / f'''\
                vk.a_neg = P.G1Point({vk.a.negated()});
                vk.b = P.G2Point({vk.b});
                vk.gamma = P.G2Point({vk.gamma});
                vk.delta = P.G2Point({vk.delta});''' * [
                f'vk.gamma_abc[{idx}] = P.G1Point({str(g)});''' for idx, g in enumerate(vk.gamma_abc)] // f'''\
            }}

            function {cfg.verification_function_name}(uint[8] memory proof_, uint[] memory {cfg.zk_in_name}, uint[] memory {cfg.zk_out_name}) public {{''' / f'''\
                // Check if input size correct
                require({cfg.zk_in_name}.length == {circuit.in_size_trans});

                // Check if output size correct
                require({cfg.zk_out_name}.length == {circuit.out_size_trans});''' * ((

                ['\n// Check that inputs do not overflow'] +
                [f'require({pi} < {self.snark_scalar_field_var_name});' for pi in potentially_overflowing_pi] + ['\n']) if potentially_overflowing_pi else '') * f'''\
                // Create proof and vk data structures
                Proof memory proof;
                proof.a = P.G1Point(proof_[0], proof_[1]);
                proof.b = P.G2Point([proof_[2], proof_[3]], [proof_[4], proof_[5]]);
                proof.c = P.G1Point(proof_[6], proof_[7]);
                Vk memory vk = getVk();

                // Compute linear combination of public inputs''' * (
                f'uint256 {self.hash_var_name} = uint256(sha256(abi.encodePacked({cfg.zk_in_name}, {cfg.zk_out_name})) >> {256 - bn128_scalar_field_bits});' if should_hash else '') * \
                f"P.G1Point memory lc = {(f'vk.gamma_abc[1].scalar_mul({first_pi})' if first_pi != '1' else f'vk.gamma_abc[1]')};" * [
                f"lc = lc.add({(f'vk.gamma_abc[{idx + 2}].scalar_mul({pi})' if pi != '1' else f'vk.gamma_abc[{idx + 2}]')});" for idx, pi in enumerate(primary_inputs[1:])] * '''\
                lc = lc.add(vk.gamma_abc[0]);

                // Verify proof
                require(P.pairingProd4(proof.a, proof.b,
                                       lc.negate(), vk.gamma,
                                       proof.c.negate(), vk.delta,
                                       vk.a_neg, vk.b), "invalid proof");''' // \
            '}' // \
        '}'

        return x.text
