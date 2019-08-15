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
contract ReceiveVerification {
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
        vk.A = Pairing.G2Point([0x1185d300b75821b5efe12931199da89214097049d5fbc615c1b6db67fac15bac, 0x65427074d52a9120c3f85edb77f7d7775e20588fd9cb5898e82ab6646a4c80d], [0x253b237c8413794a06be3e15b83e1f70c873ac12de868625cc89decdb06c3326, 0x4daf5027538875b503f9c448547b7ac4eedc07ceefea0dd2ea0a1050529c82c]);
        vk.B = Pairing.G1Point(0x2366d3d2bce394f1c39263f4914f4c327461adabeaf91751b1f23fe0c353, 0xad7995240fb56a7fc82719a590861821847ad8f374dec821a7bb7f5eedc519f);
        vk.C = Pairing.G2Point([0x143eb66d6805790b855ce958d4a22e402c80a21271a066bb6e1b299ad5974af, 0x27824c538bb3fa97a8d3fb8302d6ad7e382a5289d80d0332fa60f34a6358d7f9], [0xb681a53e8e2d73092fc632aa6e726f85c5c17915c5af1254e896c90419c69b3, 0x8b907e2375b3892cb0885884d36dde17a928241613ba80096fce8eea5554cd6]);
        vk.gamma = Pairing.G2Point([0x237456bda65f85bc828e4a65ea9ffd1b172f801bc0e4c0e5286a13c7a5412b34, 0x1c300734f159396ca2c4b2d3ee5390a170c7e29ad465aa9c1ce5e61df12b6da1], [0x24b0a0a99239c1505b522fbed5129383c1f02fc3eff31f994a9da6b17c0548b1, 0x182c80429d2606bed4b23cbf168e5cdf006b5b09bd638fc64f7d3d01a588c8e3]);
        vk.gammaBeta1 = Pairing.G1Point(0x1b4d23216ff9eb36d622d7b26b9625b39b2eaaa206b9fac2b369a497e3d77089, 0x61687902010eca6841981081121243bb5036c20143fdd36b960d6bb24cda222);
        vk.gammaBeta2 = Pairing.G2Point([0x2b3810679ac9733faf2c616e889e8dd0b1319a57d1ef7d0f1a03b7f1ccea2426, 0x210e3e59c747422aac73fb8b1ae4c6ccbddb5389e4b11c3b97ed859fd2118093], [0x2b997c51b40aa36f73b4fb48c374e65de2273dca91958d21ec34090bac5c909f, 0x2fd695571a17f49e1081c8d93e466b888e369831790c8b8dc822de7bcc03113e]);
        vk.Z = Pairing.G2Point([0x1892e21e3f3e0cdbacfc18f716178cb3670eabe4dcf7868203358e014cd30b73, 0x28d2cc6fdc5bb933514506cc02ac81aff6eb128ad5f66fcdf30b5c5f2e82273d], [0xa48337a8d56d9d321cd34184fb73fbfe5be617238e31f5229e6475621697f54, 0x2f14ea3283c37d84fa3033d6215aa7ec12783792714a0a9da0956ea91b6ecd34]);
        vk.IC = new Pairing.G1Point[](5);
        vk.IC[0] = Pairing.G1Point(0x2833a679a8e06540d0c90d13288b83f9aefd31445e387c459fa08139dbe3769a, 0x13c615ed42b6f4b885323c477e0dfefcea7fc8330299390e9e08029488bd52b2);
        vk.IC[1] = Pairing.G1Point(0x1e248a6fea132957557bc3f49db61d20dbb6fade014bae41661d84eba6bc122e, 0xdb89c36f802c01d288bc4d9e9bf9a21889212b2f4c9a32b5aff1e417bfd0e9d);
        vk.IC[2] = Pairing.G1Point(0x17529f9c8580b5a640d89322c8c08c2b5aabc69d7135f680bce5d84ca07078e6, 0x9647f7aee17f829fe044665e8e3bbe186d99979de761ca085dd4f787a9510c8);
        vk.IC[3] = Pairing.G1Point(0x2881692797adc1fef7a50d80b61805e1657e94f16d2e8587ac632f23f0104daa, 0x2bcb71ccda420432e56ec7cf05a24f2dcc571c422d8246fe55a77313cd747a2a);
        vk.IC[4] = Pairing.G1Point(0x2b4b07155c6868f09f6cf2772f76ea4e2841ee078d7bd03802bd09ab230dcfce, 0x303ae14295a65c690930b63a77e82daf96fc22a06b74bdddc43c532810b5f037);
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
