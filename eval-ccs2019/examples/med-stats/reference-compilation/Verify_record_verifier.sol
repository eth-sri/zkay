// 
// def dec(field msg, field key) -> (field):
// 	return msg - key
// 
// def enc(field msg, field R, field key) -> (field):
// 	// artificial constraints ensuring every variable is used
// 	field impossible = if R == 0 && R == 1 then 1 else 0 fi
// 	impossible == 0
// 	return msg + key
// 
// import "hashes/sha256/512bitPacked.code" as sha256packed
// 
// def checkHash(field[12] inputs, field[2] expectedHash) -> (field):
// 	field[2] hash = [0, inputs[0]]
// 	for field i in 1..12 do
// 		field[4] toHash = [hash[0], hash[1], 0, inputs[i]]
// 		hash = sha256packed(toHash)
// 	endfor
// 	
// 	hash[0] == expectedHash[0]
// 	hash[1] == expectedHash[1]
// 	return 1
// 
// 
// // genHelper0: bool@me r
// // genHelper0PK: bool@me r
// // genHelper1: r
// // genParam0: reveal(r, pat)
// // genParam0PK: reveal(r, pat)
// // genHelper2: count
// // genHelper4: r
// // genParam1: r ? reveal(1, me) : reveal(0, me)
// // genParam1PK: r ? reveal(1, me) : reveal(0, me)
// // genHelper3: (r ? reveal(1, me) : reveal(0, me))
// // genParam2: count + (r ? reveal(1, me) : reveal(0, me))
// // genParam2PK: count + (r ? reveal(1, me) : reveal(0, me))
// def main(private field genHelper0, private field genHelper0Value, private field genHelper0R, private field genHelper0PK, private field genHelper1, private field genHelper1SK, private field genParam0, private field genParam0R, private field genParam0PK, private field genHelper2, private field genHelper2SK, private field genHelper4, private field genHelper4SK, private field genParam1, private field genParam1R, private field genParam1PK, private field genHelper3, private field genHelper3SK, private field genParam2, private field genParam2R, private field genParam2PK, field inputHash0, field inputHash1) -> (field):
// 	1 == checkHash([genHelper0, genHelper0PK, genHelper1, genParam0, genParam0PK, genHelper2, genHelper4, genParam1, genParam1PK, genHelper3, genParam2, genParam2PK], [inputHash0, inputHash1])
// 	genHelper0 == enc(genHelper0Value, genHelper0R, genHelper0PK)
// 	field genParam0Dec = dec(genHelper1, genHelper1SK)
// 	genParam0 == enc(genParam0Dec, genParam0R, genParam0PK)
// 	field genParam1Dec = if dec(genHelper4, genHelper4SK) == 1 then 1 else 0 fi
// 	genParam1 == enc(genParam1Dec, genParam1R, genParam1PK)
// 	field genParam2Dec = dec(genHelper2, genHelper2SK) + dec(genHelper3, genHelper3SK)
// 	genParam2 == enc(genParam2Dec, genParam2R, genParam2PK)
// 	return 1
pragma solidity ^0.5.0;
import "./verify_libs.sol";


contract Verify_record {
    using Pairing for *;
    struct VerifyingKey {
        Pairing.G2Point H;
        Pairing.G1Point Galpha;
        Pairing.G2Point Hbeta;
        Pairing.G1Point Ggamma;
        Pairing.G2Point Hgamma;
        Pairing.G1Point[] query;
    }
    struct Proof {
        Pairing.G1Point A;
        Pairing.G2Point B;
        Pairing.G1Point C;
    }
    function verifyingKey() pure internal returns (VerifyingKey memory vk) {
        vk.H = Pairing.G2Point([uint256(0x0f1fedafe9f49c77f3f48187d1bea43a78c1c2fc152ae8cd86e804d41ffa43fc), uint256(0x2e9e750891347c97d2ee2f028efeac39b8ea242f5c6e45f06c258da5a8d77550)], [uint256(0x27af659d6c58085ff5942eb2b27b0d13067bc0f8d02cbb3023d894245bb54cbf), uint256(0x06e66922ff787bd2dbb161d393d8dc0549b7833c7b394e3d25d5b939828420c8)]);
        vk.Galpha = Pairing.G1Point(uint256(0x220cbb301213e9232a2b4e84787e7b8526c0b3a8a4f6f1889767816acfde2d26), uint256(0x0e9aff18d1efbe23689eb4ca9005c14feaeee861a111d3a40f189b092aaf51c3));
        vk.Hbeta = Pairing.G2Point([uint256(0x1ce6d4e1cfcefd0a891c8e911fae7c30a75dfa6680c32664d2c6721adbb8df99), uint256(0x2a667cd402719baf0e93c9020ab94ea74b4143d29671562bf2f36bab579286de)], [uint256(0x2ca31045656d29bfd34b67585b7a7255521ff97deb7a07c1bc3b8c5d11941f66), uint256(0x0b930aefb90f4ef7662d6868c26d2e2d99d7ffaac3e62ff14e9788045421f402)]);
        vk.Ggamma = Pairing.G1Point(uint256(0x227f02e356d643150613adb964793131916cd0af945bd77f170118d3abcec649), uint256(0x2364dc6f78c3904fc4719e73c97f58a21420404e813840831fc685425c9350b0));
        vk.Hgamma = Pairing.G2Point([uint256(0x0c7fb225c9386f80d607f0f19d8a7b3a3d3b436b81639b5bafee999f0b9cd9c8), uint256(0x1405d1c86e548a6c127fcf59efc20d9cb62a6734da52970173861ab787e03e1c)], [uint256(0x1260e913301a65dc17d50783053086a0f5a309ba7a1c88afdcd777c84dfb5425), uint256(0x2f9c537783ee818cd4c1fe23f71fc38394a5e0ea35db3656796e33421eef6659)]);
        vk.query = new Pairing.G1Point[](4);
        vk.query[0] = Pairing.G1Point(uint256(0x0e7d7e692876bf10bcc54d4f1f0d777550c822bcc731b0f2348c15c3c777e770), uint256(0x2421319d4472e31c93620e9c9472fa1e997c23f8bb2181346c2813184931496e));
        vk.query[1] = Pairing.G1Point(uint256(0x077a6b76293fe2628278cac48bec14f18de97a8d074d3c969663b70b41b2c216), uint256(0x06a0bbe996e0db17d52ce5de90476389aef63a7d92cde6280cf515c580320511));
        vk.query[2] = Pairing.G1Point(uint256(0x1932f1ce06edce1232a82e4e1858f02cbe6a7de81bfe5b4ca2e47aca203645b0), uint256(0x1d2128a5ba742a31109e58ea5e8e49d11258bab7177292dc3535dc415482e092));
        vk.query[3] = Pairing.G1Point(uint256(0x16d44a2e0ffb4c0d80df4a6504e307ee4238d645b95e05c7aab2998c92f12bff), uint256(0x1baedbeb580660adf1d4f940ecea407570865041485965cd5eb6a95cb82108b3));
    }
    function verify(uint[] memory input, Proof memory proof) internal returns (uint) {
        VerifyingKey memory vk = verifyingKey();
        require(input.length + 1 == vk.query.length);
        // Compute the linear combination vk_x
        Pairing.G1Point memory vk_x = Pairing.G1Point(0, 0);
        for (uint i = 0; i < input.length; i++)
            vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.query[i + 1], input[i]));
        vk_x = Pairing.addition(vk_x, vk.query[0]);
        /**
         * e(A*G^{alpha}, B*H^{beta}) = e(G^{alpha}, H^{beta}) * e(G^{psi}, H^{gamma})
         *                              * e(C, H)
         * where psi = \sum_{i=0}^l input_i pvk.query[i]
         */
        if (!Pairing.pairingProd4(vk.Galpha, vk.Hbeta, vk_x, vk.Hgamma, proof.C, vk.H, Pairing.negate(Pairing.addition(proof.A, vk.Galpha)), Pairing.addition(proof.B, vk.Hbeta))) return 1;
        /**
         * e(A, H^{gamma}) = e(G^{gamma}, B)
         */
        if (!Pairing.pairingProd2(proof.A, vk.Hgamma, Pairing.negate(vk.Ggamma), proof.B)) return 2;
        return 0;
    }
    event Verified(string s);
    function verifyTx(
            uint[2] memory a,
            uint[2][2] memory b,
            uint[2] memory c,
            uint[3] memory input
        ) public returns (bool r) {
        Proof memory proof;
        proof.A = Pairing.G1Point(a[0], a[1]);
        proof.B = Pairing.G2Point([b[0][0], b[0][1]], [b[1][0], b[1][1]]);
        proof.C = Pairing.G1Point(c[0], c[1]);
        uint[] memory inputValues = new uint[](input.length);
        for(uint i = 0; i < input.length; i++){
            inputValues[i] = input[i];
        }
        if (verify(inputValues, proof) == 0) {
            emit Verified("Transaction successfully verified.");
            return true;
        } else {
            return false;
        }
    }
	function check_verify(uint[8] memory proof, uint[3] memory input) public{
		require(verifyTx(
		[proof[0], proof[1]],
		[[proof[2], proof[3]], [proof[4], proof[5]]],
		[proof[6], proof[7]],
		input));
	}

}
