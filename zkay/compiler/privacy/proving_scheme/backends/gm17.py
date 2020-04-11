"""
This module defines the verification key, proof and verification contract format for the GM17 proving scheme

See "Snarky Signatures: Minimal Signatures of Knowledge from Simulation-Extractable SNARKs", Jens Groth and Mary Maller, IACR-CRYPTO-2017
https://eprint.iacr.org/2017/540
"""

from typing import List

from zkay.config import cfg

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.library_contracts import bn128_scalar_field, bn128_scalar_field_bits
from zkay.compiler.privacy.proving_scheme.proving_scheme import ProvingScheme, G1Point, G2Point, VerifyingKey
from zkay.utils.multiline_formatter import MultiLineFormatter


class ProvingSchemeGm17(ProvingScheme):
    name = 'gm17'

    class VerifyingKey(VerifyingKey):
        def __init__(self, h: G2Point, g_alpha: G1Point, h_beta: G2Point, g_gamma: G1Point, h_gamma: G2Point,
                     query: List[G1Point]):
            self.h = h
            self.g_alpha = g_alpha
            self.h_beta = h_beta
            self.g_gamma = g_gamma
            self.h_gamma = h_gamma
            self.query = query

        @classmethod
        def create_dummy_key(cls):
            p1 = G1Point('0', '0')
            p2 = G2Point('0', '0', '0', '0')
            return cls(p2, p1, p2, p1, p2, [p1, p1])

    def generate_verification_contract(self, verification_key: VerifyingKey, circuit: CircuitHelper, primary_inputs: List[str],
                                       prover_key_hash: bytes) -> str:
        vk = verification_key
        should_hash = cfg.should_use_hash(circuit)

        query_length = len(vk.query)
        assert query_length == len(primary_inputs) + 1

        assert primary_inputs, "No public inputs"
        first_pi = primary_inputs[0]
        potentially_overflowing_pi = [pi for pi in primary_inputs if pi not in ['1', self.hash_var_name]]

        # Verification contract uses the pairing library from ZoKrates (MIT license)
        # https://github.com/Zokrates/ZoKrates/blob/d8cde9e1c060cc654413f01c8414ea4eaa955d87/zokrates_core/src/proof_system/bn128/utils/solidity.rs#L398
        x = MultiLineFormatter() * f'''\
        pragma solidity {cfg.zkay_solc_version_compatibility};

        import {{ Pairing, G1Point as G1, G2Point as G2 }} from "{ProvingScheme.verify_libs_contract_filename}";

        contract {circuit.get_verification_contract_name()} {{''' / f'''\
            using Pairing for G1;
            using Pairing for G2;

            bytes32 public constant {cfg.prover_key_hash_name} = 0x{prover_key_hash.hex()};
            uint256 constant {self.snark_scalar_field_var_name} = {bn128_scalar_field};

            struct Proof {{
                G1 a;
                G2 b;
                G1 c;
            }}

            struct Vk {{
                G2 h;
                G1 g_alpha;
                G2 h_beta;
                G1 g_gamma_neg;
                G2 h_gamma;
                G1[{query_length}] query;
            }}

            function getVk() pure internal returns(Vk memory vk) {{''' / f'''\
                vk.h = G2({vk.h});
                vk.g_alpha = G1({vk.g_alpha});
                vk.h_beta = G2({vk.h_beta});
                vk.g_gamma_neg = G1({vk.g_gamma.negated()});
                vk.h_gamma = G2({vk.h_gamma});''' * [
                f'vk.query[{idx}] = G1({q});''' for idx, q in enumerate(vk.query)] // f'''\
            }}

            function {cfg.verification_function_name}(uint[8] memory proof_, uint[] memory {cfg.zk_in_name}, uint[] memory {cfg.zk_out_name}) public {{''' / f'''\
                // Check if input size correct
                require({cfg.zk_in_name}.length == {circuit.in_size_trans}, "Wrong public input length");

                // Check if output size correct
                require({cfg.zk_out_name}.length == {circuit.out_size_trans}, "Wrong public output length");''' * ((

                ['\n// Check that inputs do not overflow'] +
                [f'require({pi} < {self.snark_scalar_field_var_name});' for pi in potentially_overflowing_pi] + ['\n']) if potentially_overflowing_pi else '') * f'''\
                // Create proof and vk data structures
                Proof memory proof;
                proof.a = G1(proof_[0], proof_[1]);
                proof.b = G2([proof_[2], proof_[3]], [proof_[4], proof_[5]]);
                proof.c = G1(proof_[6], proof_[7]);
                Vk memory vk = getVk();

                // Compute linear combination of public inputs''' * (
                f'uint256 {self.hash_var_name} = uint256(sha256(abi.encodePacked({cfg.zk_in_name}, {cfg.zk_out_name})) >> {256 - bn128_scalar_field_bits});' if should_hash else '') * \
                f"G1 memory lc = {(f'vk.query[1].scalar_mul({first_pi})' if first_pi != '1' else f'vk.query[1]')};" * [
                f"lc = lc.add({(f'vk.query[{idx + 2}].scalar_mul({pi})' if pi != '1' else f'vk.query[{idx + 2}]')});" for idx, pi in enumerate(primary_inputs[1:])] * '''\
                lc = lc.add(vk.query[0]);

                // Verify proof
                require(Pairing.pairingProd2(proof.a, vk.h_gamma,
                                             vk.g_gamma_neg, proof.b), "invalid proof 1/2");
                require(Pairing.pairingProd4(vk.g_alpha, vk.h_beta,
                                             lc, vk.h_gamma,
                                             proof.c, vk.h,
                                             proof.a.add(vk.g_alpha).negate(), proof.b.add(vk.h_beta)), "invalid proof 2/2");''' // \
            '}' // \
        '}'

        return str(x)
