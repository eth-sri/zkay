// This file is MIT Licensed.
//
// Copyright 2017 Christian Reitwiessner
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

pragma solidity ^0.4.14;
library Pairing {
    struct G1Point {
        uint X;
        uint Y;
    }
    // Encoding of field elements is: X[0] * z + X[1]
    struct G2Point {
        uint[2] X;
        uint[2] Y;
    }
    /// @return the generator of G1
    function P1() internal returns (G1Point) {
        return G1Point(1, 2);
    }
    /// @return the generator of G2
    function P2() internal returns (G2Point) {
        return G2Point(
            [11559732032986387107991004021392285783925812861821192530917403151452391805634,
             10857046999023057135944570762232829481370756359578518086990519993285655852781],
            [4082367875863433681332203403145435568316851327593401208105741076214120093531,
             8495653923123431417604973247489272438418190587263600148770280649306958101930]
        );
    }
    /// @return the negation of p, i.e. p.add(p.negate()) should be zero.
    function negate(G1Point p) internal returns (G1Point) {
        // The prime q in the base field F_q for G1
        uint q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
        if (p.X == 0 && p.Y == 0)
            return G1Point(0, 0);
        return G1Point(p.X, q - (p.Y % q));
    }
    /// @return the sum of two points of G1
    function add(G1Point p1, G1Point p2) internal returns (G1Point r) {
        uint[4] memory input;
        input[0] = p1.X;
        input[1] = p1.Y;
        input[2] = p2.X;
        input[3] = p2.Y;
        bool success;
        assembly {
            success := call(sub(gas, 2000), 6, 0, input, 0xc0, r, 0x60)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid }
        }
        require(success);
    }
    /// @return the product of a point on G1 and a scalar, i.e.
    /// p == p.mul(1) and p.add(p) == p.mul(2) for all points p.
    function mul(G1Point p, uint s) internal returns (G1Point r) {
        uint[3] memory input;
        input[0] = p.X;
        input[1] = p.Y;
        input[2] = s;
        bool success;
        assembly {
            success := call(sub(gas, 2000), 7, 0, input, 0x80, r, 0x60)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid }
        }
        require (success);
    }
    /// @return the result of computing the pairing check
    /// e(p1[0], p2[0]) *  .... * e(p1[n], p2[n]) == 1
    /// For example pairing([P1(), P1().negate()], [P2(), P2()]) should
    /// return true.
    function pairing(G1Point[] p1, G2Point[] p2) internal returns (bool) {
        require(p1.length == p2.length);
        uint elements = p1.length;
        uint inputSize = elements * 6;
        uint[] memory input = new uint[](inputSize);
        for (uint i = 0; i < elements; i++)
        {
            input[i * 6 + 0] = p1[i].X;
            input[i * 6 + 1] = p1[i].Y;
            input[i * 6 + 2] = p2[i].X[0];
            input[i * 6 + 3] = p2[i].X[1];
            input[i * 6 + 4] = p2[i].Y[0];
            input[i * 6 + 5] = p2[i].Y[1];
        }
        uint[1] memory out;
        bool success;
        assembly {
            success := call(sub(gas, 2000), 8, 0, add(input, 0x20), mul(inputSize, 0x20), out, 0x20)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid }
        }
        require(success);
        return out[0] != 0;
    }
    /// Convenience method for a pairing check for two pairs.
    function pairingProd2(G1Point a1, G2Point a2, G1Point b1, G2Point b2) internal returns (bool) {
        G1Point[] memory p1 = new G1Point[](2);
        G2Point[] memory p2 = new G2Point[](2);
        p1[0] = a1;
        p1[1] = b1;
        p2[0] = a2;
        p2[1] = b2;
        return pairing(p1, p2);
    }
    /// Convenience method for a pairing check for three pairs.
    function pairingProd3(
            G1Point a1, G2Point a2,
            G1Point b1, G2Point b2,
            G1Point c1, G2Point c2
    ) internal returns (bool) {
        G1Point[] memory p1 = new G1Point[](3);
        G2Point[] memory p2 = new G2Point[](3);
        p1[0] = a1;
        p1[1] = b1;
        p1[2] = c1;
        p2[0] = a2;
        p2[1] = b2;
        p2[2] = c2;
        return pairing(p1, p2);
    }
    /// Convenience method for a pairing check for four pairs.
    function pairingProd4(
            G1Point a1, G2Point a2,
            G1Point b1, G2Point b2,
            G1Point c1, G2Point c2,
            G1Point d1, G2Point d2
    ) internal returns (bool) {
        G1Point[] memory p1 = new G1Point[](4);
        G2Point[] memory p2 = new G2Point[](4);
        p1[0] = a1;
        p1[1] = b1;
        p1[2] = c1;
        p1[3] = d1;
        p2[0] = a2;
        p2[1] = b2;
        p2[2] = c2;
        p2[3] = d2;
        return pairing(p1, p2);
    }
}
contract DataVerifier {
    using Pairing for *;
    struct VerifyingKey {
        Pairing.G2Point A;
        Pairing.G1Point B;
        Pairing.G2Point C;
        Pairing.G2Point gamma;
        Pairing.G1Point gammaBeta1;
        Pairing.G2Point gammaBeta2;
        Pairing.G2Point Z;
        Pairing.G1Point[] IC;
    }
    struct Proof {
        Pairing.G1Point A;
        Pairing.G1Point A_p;
        Pairing.G2Point B;
        Pairing.G1Point B_p;
        Pairing.G1Point C;
        Pairing.G1Point C_p;
        Pairing.G1Point K;
        Pairing.G1Point H;
    }
    function verifyingKey() internal returns (VerifyingKey vk) {
        vk.A = Pairing.G2Point([0x86eec726dac16a5ecec5a0f86b47d19cf087e52d5ce1f4e9216201b57eaa0b0, 0x1312983d4b863f83cea3c8d341faaf14ae4253c7b5afd6aab2de07a4da59df02], [0x148402e18a08ac0d911ef94f343c472284f8ba8e21fe2a1d392d2cdda837789, 0x13fefc38715797c7c438079d947388e814037dac009e88b0c9ec4181f1c96de]);
        vk.B = Pairing.G1Point(0x2b792789fb7f0fd32b1966f40ded056043242763122da1892e57d161a265ae31, 0x461f68f90cdc962a855e0940a0a802c3dd1931cbd99b9979738efa741e4ce0e);
        vk.C = Pairing.G2Point([0x21234504c8325101d094b4f3c83031b6218ae3af36a74bcdddc72559e12356b6, 0x2444bc5c310bbdeee13b51655977a521d05c8df8623430e67a3bdc3c786edcc3], [0x25db37524c88b40d6455a88c480d7de7c937badbdf6c3794206af21db1ce41eb, 0x218206195fdf2e695491bd65dd7ce520f775a8089011b0fbed79519eafd67e4e]);
        vk.gamma = Pairing.G2Point([0x2266a42a54920c0641fb0edd056f0afa217f5fcc509226d33b45a0531a099564, 0x4c3344fe31cf1462fa211eae389caee0a35e85edba7a78e3d5bb8d35a2e1f4c], [0x216373b05945006cd1ed8e409a95cde05d97dd31d48ac3a62657182519308389, 0x24f048e2a94a0179375c7ad9c39480aa5cccdd43b8dde705ff94bbdb5a58e185]);
        vk.gammaBeta1 = Pairing.G1Point(0x9d27bc61a0331a58c98da07d3c3f1e1422c4d9c7c606deefdeb4306c43f5c07, 0x2156452703ae7d0a676bf7f8bbf1be468e20bd5d103f4b7f425dc929f1b3ac9c);
        vk.gammaBeta2 = Pairing.G2Point([0xaa91ca1cbeed2514a5c9241a5705d1fef48489809700ca3e97fb2212705aa8b, 0x14e300269af045dacbe9897202ea874cba09e43df42800e9c82846c7a3961bd4], [0x26b9d9134309c1a16a6215016c39896c30f8e5d9c89668ef9cef3ba298d8bef8, 0xc9f4d3c6f98638e1f826883cb5ccd82db5b046b734d2813b218238f0e870a6e]);
        vk.Z = Pairing.G2Point([0x241afad90ab26958598befc3d32138b0e72d96dfde95c342dac150c220bc4faf, 0x226b0bfe5e525ba77721ab03dc393f795ad16b48d9b153a7e4d0f98e30980c6b], [0x26f734e9cd1246b022e5d5b0c1900f0650853534e6321abd5397b5a2de3fee0f, 0x1c34604959e118012f6fe49e76973c2910fcb2c208a98696aa4046a6b71b950f]);
        vk.IC = new Pairing.G1Point[](5);
        vk.IC[0] = Pairing.G1Point(0x17e596380a3ab15f3999642f7dd350f32477997e456816ab9e9c2b1eeb3a0a4b, 0x910797feb52833d6cccad6bca7c19e960e750a8023199bae9df08d243e64bc2);
        vk.IC[1] = Pairing.G1Point(0x2fab34bd60e323691e822e1fa4052079137556e881c7e240ed6e65c4332e9a6b, 0x14ee89ab33eec10972182b9477b7edd4f651649e9ae02cf39bc0985323c43997);
        vk.IC[2] = Pairing.G1Point(0x219035ce36cf010e570f720c522a3d1409a9e3008e4553de80086444f39efa24, 0x14d127f6f61bda5f23f86d4ac5e04a64890c025f3081a9a06a25f49aa6f51486);
        vk.IC[3] = Pairing.G1Point(0xc53806054e9174bc2ad41258618a4238010ab2e509e311c85b6a3a7c2959b7d, 0x216664332fb4e88f4d4b32832cdc6f76ae949122613fd028305c0c272267608a);
        vk.IC[4] = Pairing.G1Point(0x1adc6d333b80f380176fd6498ce7df9e5ac59a729aaa19cd1d888184703ccd49, 0x14ec25990ea37035ad9298d2eff142d612f38de98e1b7718c381f7892ba76e71);
    }
    function verify(uint[] input, Proof proof) internal returns (uint) {
        VerifyingKey memory vk = verifyingKey();
        require(input.length + 1 == vk.IC.length);
        // Compute the linear combination vk_x
        Pairing.G1Point memory vk_x = Pairing.G1Point(0, 0);
        for (uint i = 0; i < input.length; i++)
            vk_x = Pairing.add(vk_x, Pairing.mul(vk.IC[i + 1], input[i]));
        vk_x = Pairing.add(vk_x, vk.IC[0]);
        if (!Pairing.pairingProd2(proof.A, vk.A, Pairing.negate(proof.A_p), Pairing.P2())) return 1;
        if (!Pairing.pairingProd2(vk.B, proof.B, Pairing.negate(proof.B_p), Pairing.P2())) return 2;
        if (!Pairing.pairingProd2(proof.C, vk.C, Pairing.negate(proof.C_p), Pairing.P2())) return 3;
        if (!Pairing.pairingProd3(
            proof.K, vk.gamma,
            Pairing.negate(Pairing.add(vk_x, Pairing.add(proof.A, proof.C))), vk.gammaBeta2,
            Pairing.negate(vk.gammaBeta1), proof.B
        )) return 4;
        if (!Pairing.pairingProd3(
                Pairing.add(vk_x, proof.A), proof.B,
                Pairing.negate(proof.H), vk.Z,
                Pairing.negate(proof.C), Pairing.P2()
        )) return 5;
        return 0;
    }
    event Verified(string);
    function verifyTx(
            uint[2] a,
            uint[2] a_p,
            uint[2][2] b,
            uint[2] b_p,
            uint[2] c,
            uint[2] c_p,
            uint[2] h,
            uint[2] k,
            uint[4] input
        ) returns (bool r) {
        Proof memory proof;
        proof.A = Pairing.G1Point(a[0], a[1]);
        proof.A_p = Pairing.G1Point(a_p[0], a_p[1]);
        proof.B = Pairing.G2Point([b[0][0], b[0][1]], [b[1][0], b[1][1]]);
        proof.B_p = Pairing.G1Point(b_p[0], b_p[1]);
        proof.C = Pairing.G1Point(c[0], c[1]);
        proof.C_p = Pairing.G1Point(c_p[0], c_p[1]);
        proof.H = Pairing.G1Point(h[0], h[1]);
        proof.K = Pairing.G1Point(k[0], k[1]);
        uint[] memory inputValues = new uint[](input.length);
        for(uint i = 0; i < input.length; i++){
            inputValues[i] = input[i];
        }
        if (verify(inputValues, proof) == 0) {
            Verified("Transaction successfully verified.");
            return true;
        } else {
            return false;
        }
    }
}
