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
// def checkHash(field[2] inputs, field[2] expectedHash) -> (field):
// 	field[2] hash = [0, inputs[0]]
// 	for field i in 1..2 do
// 		field[4] toHash = [hash[0], hash[1], 0, inputs[i]]
// 		hash = sha256packed(toHash)
// 	endfor
// 	
// 	hash[0] == expectedHash[0]
// 	hash[1] == expectedHash[1]
// 	return 1
// 
// 
// // genParam0: reveal(0, hospital)
// // genParam0PK: reveal(0, hospital)
// def main(private field genParam0, private field genParam0R, private field genParam0PK, field inputHash0, field inputHash1) -> (field):
// 	1 == checkHash([genParam0, genParam0PK], [inputHash0, inputHash1])
// 	field genParam0Dec = 0
// 	genParam0 == enc(genParam0Dec, genParam0R, genParam0PK)
// 	return 1
pragma solidity ^0.5.0;
import "./verify_libs.sol";


contract Verify_constructor {
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
        vk.H = Pairing.G2Point([uint256(0x0471db120a8136b4d595b45c8fd1d85ca350618455a3f83a0e7ec938643dd656), uint256(0x17fb2f7d13adab2b348546980d0f4a93be1b1f1a0269df49d7462d9338d82db9)], [uint256(0x058a27f5877d702540e6e115435f0daf5be6b9b33f4b83aca4c46a21a08ebbac), uint256(0x138b36a9a786e321e34136acb21a62f209cf0a8d1471b3d5ceedf7c1a8dcb6df)]);
        vk.Galpha = Pairing.G1Point(uint256(0x03a04eeb2877c8c62a7746da9f2e5c39ac19937de88b0021faf94d5740bbfcec), uint256(0x0ab23dd3c2641f2bcf0afe8b4998b32d397ae9e1f582717242c64a385f6fadfa));
        vk.Hbeta = Pairing.G2Point([uint256(0x13fb3ec32b97513cb674fc4d25c528b61f61d69cf676d63cf8b12ad2e2252d7d), uint256(0x2459d5ff6d7489c9de637c0f747c0ad2ae55774e43429d66e0433351afc9d43d)], [uint256(0x1c53fbf2f080f5c28742c33de4e037c8a66b47b5262670d98bc056a778399e9b), uint256(0x24df2abe7072a8ad1848917f2b5e1e2d303a2f4f10a60a57fe3a1a73fde9c472)]);
        vk.Ggamma = Pairing.G1Point(uint256(0x12a3b9d2f192aa6813e2e63392752f61a0c18fb7632954499acd070c31e46014), uint256(0x0050c6ab5b7a505c492b74c907ec7e49f8a9e3901de39a3fbf101d74187e9438));
        vk.Hgamma = Pairing.G2Point([uint256(0x1e30d251f1bd3dbed9e7e81119722d49c20647dd7397361faa8a608956dbf2e9), uint256(0x19b37fc3733718efa561cfa9f7a3f166321274c0f6c63fab3111a92dfed9f173)], [uint256(0x00c1e672d39caa6dc2aa2d083a308f9a7acfec259ad2f4c751967099164508e8), uint256(0x2a4a7942805e0d02409d962ff02c01ec63cabfe5e7e772ab1f9d820cbbcc94cd)]);
        vk.query = new Pairing.G1Point[](4);
        vk.query[0] = Pairing.G1Point(uint256(0x1d52176ea6b349182ac77c4a800710048205e18f432cd4e53ef852da7595b4f8), uint256(0x09d3a415f7fd667183ab1fec9d982234e4b48f461e0aef1a1a20355240b99aa5));
        vk.query[1] = Pairing.G1Point(uint256(0x2bd570bd0d4952ac9d051ff0e14834e10dce39bd6d3af49db3b4a8236529a334), uint256(0x00c64704eb5f223c575beed3e49ec407cb566ab1a5ed1bf23c9d60c10498cfae));
        vk.query[2] = Pairing.G1Point(uint256(0x0a5e7e22a185a38193bbf6711bee5fcd32ce5378ec3859bd21abb24ae5499447), uint256(0x2e614a5b02816f4a1b9f7057d69c0b1845158f44a52110efe20ce12b422c9c8f));
        vk.query[3] = Pairing.G1Point(uint256(0x029bad556643d3dc395c408413a61c730fc6cf16d0c4f7e3a171e0d97858101f), uint256(0x24d771048a480036543c3c7dd69d853faf63b9f254640fe2da8f18c83ceb39d2));
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
