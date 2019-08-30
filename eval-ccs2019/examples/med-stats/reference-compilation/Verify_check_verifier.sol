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
// def checkHash(field[5] inputs, field[2] expectedHash) -> (field):
// 	field[2] hash = [0, inputs[0]]
// 	for field i in 1..5 do
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
// // genHelper2: risk[me]
// // genParam0: reveal(r == risk[me], all)
// def main(private field genHelper0, private field genHelper0Value, private field genHelper0R, private field genHelper0PK, private field genHelper1, private field genHelper1SK, private field genHelper2, private field genHelper2SK, private field genParam0, field inputHash0, field inputHash1) -> (field):
// 	1 == checkHash([genHelper0, genHelper0PK, genHelper1, genHelper2, genParam0], [inputHash0, inputHash1])
// 	genHelper0 == enc(genHelper0Value, genHelper0R, genHelper0PK)
// 	genParam0 == if dec(genHelper1, genHelper1SK) == dec(genHelper2, genHelper2SK) then 1 else 0 fi
// 	return 1
pragma solidity ^0.5.0;
import "./verify_libs.sol";


contract Verify_check {
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
        vk.H = Pairing.G2Point([uint256(0x133db21e90d871c2348984dccb9f14d6778a77f0da8df89002b930dfb5520b40), uint256(0x222975b89c7106f517ca5d46dfbad57e8cbe126080ad65bc439b43faa28568a4)], [uint256(0x01b12d2d271e8c8b6a013d7b233a715e5ceb24cd5928139dc66cb68fdaacdeef), uint256(0x1c2ad51033581a803280dbc517623a5a507aaa4f50b304b6f01e6ed68a8ec3f1)]);
        vk.Galpha = Pairing.G1Point(uint256(0x1e7bccd8efec4985486afdd83fd73ef1c10eec2c509c6889ac30de3be28f4b41), uint256(0x00bb6b35d51af7c1b9d9c862116c74e11895503c4154ec3e0135ec07f6bf115d));
        vk.Hbeta = Pairing.G2Point([uint256(0x0f07f879adeea624afb373bb7b465b47e1e78c16b9133d94468f3bcba982eea4), uint256(0x10266a12625707c17d6da829af3e5ccaf3cf74006c1ff09debc1fc31b6b4a226)], [uint256(0x2bb33540225ca0de64aef5b82bc1f405fc3790aa8ce27a8d194c5bd8e4dd337b), uint256(0x1010118276b8e6caf2ef0022bd957952c3497b8e8556955744a4ef280d39d62f)]);
        vk.Ggamma = Pairing.G1Point(uint256(0x055c2169464a6192d2f106c1e2058068cd0c4487c25a27bd9f6241ed1b1cab43), uint256(0x0044f81ba12b8fa7a64fefe870137b0210e8b559625dd7301e2e9a30f670e579));
        vk.Hgamma = Pairing.G2Point([uint256(0x220ce3ea37c40517f2b176957fed7d81e1ccf92bf9899ed63f9bee5267290782), uint256(0x120f289cf135400ae60be9979f76544d65f45c40d5578f411a694070ee87a56b)], [uint256(0x0137a1aef97f0026788c281a0b7f6b420af202693425d4d5e0846f536c934b66), uint256(0x2dd1fcebde35579a6b4d7e5bba771ae47db1ba708930d14ac3916a8b2f65a851)]);
        vk.query = new Pairing.G1Point[](4);
        vk.query[0] = Pairing.G1Point(uint256(0x1af4efb22066815af8db566e60cb5ed5ea7ca1671553498f7b16b3b84bbd58ab), uint256(0x0e0e31701074e2a9331ddca1404dfd9cdf2239ac21ef5e961c1ddc94daa760bd));
        vk.query[1] = Pairing.G1Point(uint256(0x2b965a8871bde80b0cae274d4af982a849d60d1149c7dabd68d9a5fe6d261d8c), uint256(0x2f66d5b7df04cedfbc35de2c84d1b557c35525c1b83654d7cc2f60fefdd0f85b));
        vk.query[2] = Pairing.G1Point(uint256(0x2962d7cea4684ed64cf6abf62168cebced0d116ccee91143a742c934677cf456), uint256(0x2f35d7c1b43132b066d7d3dbe6069f5035b99ca6a64aee7fb40377c1962aec07));
        vk.query[3] = Pairing.G1Point(uint256(0x01016a2a47633de902c5e76f67b0f48ae0c8727d7ea5e1b6ecb8e8e8ad604a41), uint256(0x2621934543b681336f7d2ad835d6682e14f9b5bfa814bef5d972f0f4233850a6));
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
