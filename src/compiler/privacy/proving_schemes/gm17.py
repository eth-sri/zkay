from textwrap import dedent
from typing import List

from compiler.privacy.circuit_generation.circuit_generator import CircuitHelper
from compiler.privacy.proving_schemes.proving_scheme import ProvingScheme, G1Point, G2Point, Proof, VerifyingKey


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
    def __init__(self):
        super().__init__('gm17')

    def dummy_vk(self) -> VerifyingKeyGm17:
        p1 = G1Point('0', '0')
        p2 = G2Point('0', '0', '0', '0')
        return VerifyingKeyGm17(p2, p1, p2, p1, p2, [p1, p1])

    def generate_verification_contract(self, verification_key: VerifyingKeyGm17, circuit: CircuitHelper) -> str:
        vk = verification_key
        # Verification contract source (with some modifications by NB):
        # https://github.com/Zokrates/ZoKrates/blob/bb98ab1c0426ceeaa2d181fbfbfdc616b8365c6b/zokrates_core/src/proof_system/bn128/gm17.rs#L199
        indata = circuit.temp_name_factory
        inlen = indata.count
        outdata = circuit.param_name_factory
        outlen = outdata.count

        # TODO, perform input hashing to reduce query size

        return dedent(f'''\
        pragma solidity ^0.5.0;

        import "{ProvingScheme.verify_libs_contract_filename}";

        contract {circuit.get_circuit_name()} {{
            using Pairing for *;

            struct VerifyingKey {{
                Pairing.G2Point h;
                Pairing.G1Point g_alpha;
                Pairing.G2Point h_beta;
                Pairing.G1Point g_gamma;
                Pairing.G2Point h_gamma;
                Pairing.G1Point[] query;
            }}

            struct Proof {{
                Pairing.G1Point a;
                Pairing.G2Point b;
                Pairing.G1Point c;
            }}

            function verifyingKey() pure internal returns (VerifyingKey memory vk) {{
                vk.h = Pairing.G2Point({str(vk.h)});
                vk.g_alpha = Pairing.G1Point({str(vk.g_alpha)});
                vk.h_beta = Pairing.G2Point({str(vk.h_beta)});
                vk.g_gamma = Pairing.G1Point({str(vk.g_gamma)});
                vk.h_gamma = Pairing.G2Point({str(vk.h_gamma)});
                vk.query = new Pairing.G1Point[]({len(vk.query)});''' + ''.join([f'''
                vk.query[{idx}] = Pairing.G1Point({str(q)});''' for idx, q in enumerate(vk.query)]) + f'''
            }}

            function check_verify(uint[8] memory proof_{self._get_uint_param(indata)}{self._get_uint_param(outdata)}) public {{
                Proof memory proof;
                proof.a = Pairing.G1Point(proof_[0], proof_[1]);
                proof.b = Pairing.G2Point([proof_[2], proof_[3]], [proof_[4], proof_[5]]);
                proof.c = Pairing.G1Point(proof_[6], proof_[7]);

                uint256 snark_scalar_field = 21888242871839275222246405745257275088548364400416034343698204186575808495617;
                VerifyingKey memory vk = verifyingKey();
                require(vk.query.length == {inlen + outlen + 1});
                Pairing.G1Point memory vk_x = Pairing.G1Point(0, 0);''' +
                ('' if inlen == 0 else f'''
                for (uint i = 0; i < {inlen}; i++) {{
                    require({indata.base_name}[i] < snark_scalar_field);
                    vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.query[i + 1], {indata.base_name}[i]));
                }}''') +
                ('' if outlen == 0 else f'''
                for (uint i = 0; i < {outlen}; i++) {{
                    require({outdata.base_name}[i] < snark_scalar_field);
                    vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.query[i + {inlen + 1}], {outdata.base_name}[i]));
                }}''') + '''

                vk_x = Pairing.addition(vk_x, vk.query[0]);
                if (!Pairing.pairingProd4(vk.g_alpha, vk.h_beta, vk_x, vk.h_gamma, proof.c, vk.h, Pairing.negate(Pairing.addition(proof.a, vk.g_alpha)), Pairing.addition(proof.b, vk.h_beta))) {
                    require(false, "Proof verification failed at first check");
                }
                if (!Pairing.pairingProd2(proof.a, vk.h_gamma, Pairing.negate(vk.g_gamma), proof.b)) {
                    require(false, "Proof verification failed at second check");
                }
            }
        }''')
