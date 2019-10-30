from typing import List

from zkay.compiler.privacy.circuit_generation.circuit_generator import CircuitHelper
from zkay.compiler.privacy.library_contracts import should_use_hash
from zkay.compiler.privacy.proving_schemes.proving_scheme import ProvingScheme, G1Point, G2Point, Proof, VerifyingKey
from zkay.utils.multiline_formatter import MultiLineFormatter


class VerifyingKeyGm17(VerifyingKey):
    def __init__(self, h: G2Point, g_alpha: G1Point, h_beta: G2Point, g_gamma: G1Point, h_gamma: G2Point, query: List[G1Point]):
        self.h = h
        self.g_alpha = g_alpha
        self.h_beta = h_beta
        self.g_gamma = g_gamma
        self.h_gamma = h_gamma
        self.query = query


class ProofGm17(Proof):
    def __init__(self, a: G1Point, b: G2Point, c: G1Point):
        self.a = a
        self.b = b
        self.c = c


class ProvingSchemeGm17(ProvingScheme):
    name = 'gm17'

    def dummy_vk(self) -> VerifyingKeyGm17:
        p1 = G1Point('0', '0')
        p2 = G2Point('0', '0', '0', '0')
        return VerifyingKeyGm17(p2, p1, p2, p1, p2, [p1, p1])

    def generate_verification_contract(self, verification_key: VerifyingKeyGm17, circuit: CircuitHelper) -> str:
        vk = verification_key
        inputs = [(e.base_name, e.count) for e in (circuit.in_name_factory, circuit.out_name_factory) if e.count > 0]
        tot_count = sum(map(lambda x: x[1], inputs))

        if should_use_hash(tot_count):
            query_length = 2
            body = f'''\
                uint256 hash = uint256(sha256(abi.encodePacked({', '.join([n for n, _ in inputs])}))) % snark_scalar_field;
                vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.query[1], hash));'''
        else:
            query_length = tot_count + 2
            body = ''
            done_count = 0
            for var, count in inputs:
                body += f'''\
                for (uint i = 0; i < {count}; i++) {{
                    require({var}[i] < snark_scalar_field, "in_ value outside snark field bounds");
                    vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.query[i + {1 + done_count}], {var}[i]));
                }}\n'''
                done_count += count
            body += f'''\
                vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.query[{tot_count + 1}], 1));'''

        # Verification contract based on (with some modifications by NB):
        # https://github.com/Zokrates/ZoKrates/blob/bb98ab1c0426ceeaa2d181fbfbfdc616b8365c6b/zokrates_core/src/proof_system/bn128/gm17.rs#L199
        x = MultiLineFormatter() * f'''\
        pragma solidity ^0.5.0;

        import "{ProvingScheme.verify_libs_contract_filename}";

        contract {circuit.get_circuit_name()} {{''' / f'''\
            using Pairing for *;

            uint256 constant snark_scalar_field = 21888242871839275222246405745257275088548364400416034343698204186575808495617;

            struct VerifyingKey {{
                Pairing.G2Point h;
                Pairing.G1Point g_alpha;
                Pairing.G2Point h_beta;
                Pairing.G1Point g_gamma;
                Pairing.G2Point h_gamma;
                Pairing.G1Point[{query_length}] query;
            }}

            struct Proof {{
                Pairing.G1Point a;
                Pairing.G2Point b;
                Pairing.G1Point c;
            }}

            function verifyingKey() pure internal returns (VerifyingKey memory vk) {{''' / f'''\
                vk.h = Pairing.G2Point({str(vk.h)});
                vk.g_alpha = Pairing.G1Point({str(vk.g_alpha)});
                vk.h_beta = Pairing.G2Point({str(vk.h_beta)});
                vk.g_gamma = Pairing.G1Point({str(vk.g_gamma)});
                vk.h_gamma = Pairing.G2Point({str(vk.h_gamma)});''' * [
                f'vk.query[{idx}] = Pairing.G1Point({str(q)});''' for idx, q in enumerate(vk.query)] * f'''\
                return vk;''' // f'''\
            }}

            function check_verify(uint[8] memory proof_, {', '.join([f'uint[{count}] memory {var}' for var, count in inputs])}) public {{''' / '''\
                Proof memory proof;
                proof.a = Pairing.G1Point(proof_[0], proof_[1]);
                proof.b = Pairing.G2Point([proof_[2], proof_[3]], [proof_[4], proof_[5]]);
                proof.c = Pairing.G1Point(proof_[6], proof_[7]);
                VerifyingKey memory vk = verifyingKey();

                Pairing.G1Point memory vk_x = Pairing.G1Point(0, 0);''' * \
                body * '''\
                vk_x = Pairing.addition(vk_x, vk.query[0]);

                // Check if proof is correct
                if (!Pairing.pairingProd4(vk.g_alpha, vk.h_beta, vk_x, vk.h_gamma, proof.c, vk.h, Pairing.negate(Pairing.addition(proof.a, vk.g_alpha)), Pairing.addition(proof.b, vk.h_beta))) {
                    require(false, "Proof verification failed at first check");
                }
                if (!Pairing.pairingProd2(proof.a, vk.h_gamma, Pairing.negate(vk.g_gamma), proof.b)) {
                    require(false, "Proof verification failed at second check");
                }''' // \
            '}' // \
        '}'

        return x.text
