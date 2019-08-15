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
contract SendVerification {
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
        vk.A = Pairing.G2Point([0x2c90da9051fd6a0d73fbce467847cbed3497584ed7625a531f6b16dc2d39b852, 0x1abdb3cff42f447a3de856d75a35e46fed64c87fb6d8f057d4d9e87bf15ba1cb], [0x1831e2e376869c7ee62cd1718098e0712ba5708c9bbca6fcb870980a1d241174, 0x2e4d4f1991b6b2a298e244e8c1a0107a135add6d7bfa001c7c74b60dfe5b19e8]);
        vk.B = Pairing.G1Point(0x2db6d4c25b1c96fabb956f56f179a61e2d6efb52d4ff3bb79097f7db65ce33f7, 0x133a1f065ea3d71e1adbbbb35dc3807a0fb818a06a359f21856490dedea1a647);
        vk.C = Pairing.G2Point([0x2f0b75c5c59560ed60919bb09607e7737a13d48e8483a107ff1b896d55ae1d8b, 0x1caee24abb152a287ef68d59b941e03a91a85574f8619ce754298afad53a989e], [0x640ab179aa4977e6de5e791d1830ca6b44238a42e44a0283c49f62db15af84c, 0x5434d7df4ac8a23b9e7bf22f57fd2bb6ce06759d4764610d435025ca0611e3c]);
        vk.gamma = Pairing.G2Point([0xd8db0a6d6f6b0626fe6b8e674c7ed47850e89040389272df941f19cc6724019, 0x3970ef44f751fabff890a1b46811f2bad9a87d82672171d1fc2b950a39a2398], [0x2c53d6a7eb7915ddf2528b6f76a06767a8afd83a23a14944aa12726fe4da1ac, 0x8f14efc37198083e418e9acaa3f17934652e3771ea5f8d847ced445077b856e]);
        vk.gammaBeta1 = Pairing.G1Point(0x1d3543bd235f1d8b3ac1fba0ad24c833c004c7a18acd39b88cce2d691111b32a, 0x1973255ce6ffbef825d44c9ca7a12568cafd7015f3c1a51d076f5f03c5cae928);
        vk.gammaBeta2 = Pairing.G2Point([0x6a8bc53ab2f647e591bd45ef391846b549843899d0ac011d67aa0b818364187, 0x1ecd45db5044298b132a3a029499b780aac33c1680ded3976bcc486979884cdf], [0x2d3b0cdff3c3e0cb3412f6608638491426879aaac75f9d83fe8fed5119712f4f, 0x15dff93023acb2934359d53234ec2e3d386f44a0612981e90eeee3f75a4fc383]);
        vk.Z = Pairing.G2Point([0xc7d1aedebd4014cbaf109958d2e642be1e815d43362e3ca7c3372dcfe6b73fc, 0x128a793a305f4399b488323d9f6ddbd28d9a605e8b5e5a508a4e8fc5f64037b8], [0x1e7ccb3d73bc0039e79cb1b62bbcd7eab59685fb236111ac5ee3d58f1281de34, 0x696ef973f56289885f5c86b261998f5c14dfb27a590daaac86cde985addd275]);
        vk.IC = new Pairing.G1Point[](6);
        vk.IC[0] = Pairing.G1Point(0x1f9c44db2327da76e6d5c8204dc3042c73c532f14a9e38885df6d4f89d749ca8, 0x1c3b2c2d5def55a4a49774a16fa42eeea0030e80c466ed085bf132c193533163);
        vk.IC[1] = Pairing.G1Point(0x139a4bcc9e186618f3406cd1c28f33c2ffc027499c3bb1101749329a9ef1c3f4, 0x2e4cfae3005f4cc901ba5ad1d40a7ebe71a0a507e942e1032884961c86b0a922);
        vk.IC[2] = Pairing.G1Point(0x20e7a2813690e68abd5ad6b9487db45930054517d0758767106123a2a072fb2e, 0x27612cb2871c5945006ca8a38d921d80bf23c97e9d794b13092b625cb4ca2775);
        vk.IC[3] = Pairing.G1Point(0x23e1897f2a94a55ae53adc0092465d6aa428b6b9636d18138d49e8a1edfef69, 0x11e3c8a82a5b3d15f2fb7fba336dc777ae55280d97b0c190678a7e452de3698e);
        vk.IC[4] = Pairing.G1Point(0x98a66b1c87f2f7d1cbdef1b6b85741951620a78265e7da97919f3b627be19ba, 0x3cc3e1eb36f8737ff3ce2fb122f7593deb529f5bb7e966c017ab67382eff7f8);
        vk.IC[5] = Pairing.G1Point(0x2fe648fa8ab0570895b1b0d08b1981e53f64d6cbec95e09f9c9fa82aa6e3e563, 0x1bf0d506aee57c202e326985cef1d379f21569f6149d30c8eec50a27483b2c63);
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
            uint[5] input
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
