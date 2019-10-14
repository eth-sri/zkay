from textwrap import dedent
from typing import List
from os import linesep

from compiler.privacy.circuit_generation.proving_scheme import ProvingScheme, G1Point, G2Point, Proof, VerifyingKey


class VerifyingKeyGm17(VerifyingKey):
    def __init__(self, h: G2Point, g_alpha: G1Point, h_beta: G1Point, g_gamma: G1Point, h_gamma: G2Point, query: List[G1Point]):
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

    def generate_verification_contract(self, verification_key: VerifyingKeyGm17, input_length: int) -> str:
        vk = verification_key
        # Verification contract source:
        # https://github.com/Zokrates/ZoKrates/blob/bb98ab1c0426ceeaa2d181fbfbfdc616b8365c6b/zokrates_core/src/proof_system/bn128/gm17.rs#L199
        return dedent(f'''\
        contract Verifier {{
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
                vk.h= Pairing.G2Point({str(vk.h)});
                vk.g_alpha = Pairing.G1Point({str(vk.g_alpha)});
                vk.h_beta = Pairing.G2Point({str(vk.h_beta)});
                vk.g_gamma = Pairing.G1Point({str(vk.g_gamma)});
                vk.h_gamma = Pairing.G2Point({str(vk.h_gamma)});
                vk.query = new Pairing.G1Point[]({len(vk.query)});
                {linesep.join([f"vk.query[{idx}] = Pairing.G1Point({str(q)});" for idx, q in enumerate(vk.query)])}
            }}
            function verify(uint[] memory input, Proof memory proof) internal returns (uint) {{
                uint256 snark_scalar_field = 21888242871839275222246405745257275088548364400416034343698204186575808495617;
                VerifyingKey memory vk = verifyingKey();
                require(input.length + 1 == vk.query.length);
                Pairing.G1Point memory vk_x = Pairing.G1Point(0, 0);
                for (uint i = 0; i < input.length; i++) {{
                    require(input[i] < snark_scalar_field);
                    vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.query[i + 1], input[i]));
                }}
                vk_x = Pairing.addition(vk_x, vk.query[0]);
                if (!Pairing.pairingProd4(vk.g_alpha, vk.h_beta, vk_x, vk.h_gamma, proof.c, vk.h, Pairing.negate(Pairing.addition(proof.a, vk.g_alpha)), Pairing.addition(proof.b, vk.h_beta))) return 1;
                if (!Pairing.pairingProd2(proof.a, vk.h_gamma, Pairing.negate(vk.g_gamma), proof.b)) return 2;
                return 0;
            }}
            event Verified(string s);
            function verifyTx(
                    Proof memory proof,
                    uint[{input_length}] memory input
                ) public returns (bool r) {{
                uint[] memory inputValues = new uint[](input.length);
                for(uint i = 0; i < input.length; i++){{
                    inputValues[i] = input[i];
                }}
                if (verify(inputValues, proof) == 0) {{
                    emit Verified("Transaction successfully verified.");
                    return true;
                }} else {{
                    return false;
                }}
            }}
        }}''')
