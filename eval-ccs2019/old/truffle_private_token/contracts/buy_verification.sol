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
    function P1() pure internal returns (G1Point) {
        return G1Point(1, 2);
    }
    /// @return the generator of G2
    function P2() pure internal returns (G2Point) {
        return G2Point(
            [11559732032986387107991004021392285783925812861821192530917403151452391805634,
             10857046999023057135944570762232829481370756359578518086990519993285655852781],
            [4082367875863433681332203403145435568316851327593401208105741076214120093531,
             8495653923123431417604973247489272438418190587263600148770280649306958101930]
        );
    }
    /// @return the negation of p, i.e. p.addition(p.negate()) should be zero.
    function negate(G1Point p) pure internal returns (G1Point) {
        // The prime q in the base field F_q for G1
        uint q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
        if (p.X == 0 && p.Y == 0)
            return G1Point(0, 0);
        return G1Point(p.X, q - (p.Y % q));
    }
    /// @return the sum of two points of G1
    function addition(G1Point p1, G1Point p2) internal returns (G1Point r) {
        uint[4] memory input;
        input[0] = p1.X;
        input[1] = p1.Y;
        input[2] = p2.X;
        input[3] = p2.Y;
        bool success;
        assembly {
            success := call(sub(gas, 2000), 6, 0, input, 0xc0, r, 0x60)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid() }
        }
        require(success);
    }
    /// @return the product of a point on G1 and a scalar, i.e.
    /// p == p.scalar_mul(1) and p.addition(p) == p.scalar_mul(2) for all points p.
    function scalar_mul(G1Point p, uint s) internal returns (G1Point r) {
        uint[3] memory input;
        input[0] = p.X;
        input[1] = p.Y;
        input[2] = s;
        bool success;
        assembly {
            success := call(sub(gas, 2000), 7, 0, input, 0x80, r, 0x60)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid() }
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
            switch success case 0 { invalid() }
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
contract BuyVerification {
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
    function verifyingKey() pure internal returns (VerifyingKey vk) {
        vk.A = Pairing.G2Point([0x28fe17f478a866d92c8c9142aa3d391bb72289dfe73f162c3df293a41828757f, 0xb7cabf1304f5b153447e4d30743b410b59112ca50070215b08fb446975dd13f], [0x8cb94c7c57045910aa846ec33ad74f4abc775ae4d7164d0b48f475cf7eaaf98, 0x22623dd182bb1572a5e933bfc08fddc457e22aeb2b86b15e5efb458f47bb2e16]);
        vk.B = Pairing.G1Point(0x185d3493260540e92bdc6df48d794a79b57b33e0f68cd98ffa3a5caa182a6926, 0x2f960ae4d0ed79b35963a5c9a81f767ec41cc8528cf80dea969574527b2fffae);
        vk.C = Pairing.G2Point([0xd581bc8632af8fbb00c16b3adb526404884a09c5b95699ff819f920e3064e6f, 0x154ffb2e5789f0d7f8b6ade01fef7a28063fc9921f77dbbeb02d8655dd053977], [0x5edb353b6261f37cc1d92d089986da2c5eec69f638dd24d809c9c6bdf9e088a, 0x2e6d96639bd1d9dadc3d97adfa2085be1c6a000a4065157a92a9c706e3abd719]);
        vk.gamma = Pairing.G2Point([0xa401f971198ffae687884648791aa4aeff049acf0da21a72068a40bd8111f2e, 0x10479b2cc5cad321f5be1311008f032bbd00d400c8f7595a15e7e2d90ae9d14e], [0x1c7b8dbfae6640bb6888cc3d1e50d10e0faec0f9fb495aecff79782964af838a, 0x6dc216c7c6b756929f277b18a47d441792f2793dc57d0088346470d91d1a8e0]);
        vk.gammaBeta1 = Pairing.G1Point(0x3038c9db87e097bb93aabb564d4cded4eab289edbd127130350ac634c08c33f9, 0xf68e7d5058ecf50f653b0b65197e1614735e822a399cdd628e9561c75e515eb);
        vk.gammaBeta2 = Pairing.G2Point([0x13442e2b8cabe4d083a82fe866f57ac6226121f53a3352760bd80e2e52f64693, 0x7409405004b9c09d0472d6850ae871463b696b1789a68130af412ef20269c8b], [0x16e8f82231808bb14b02be5771a2ebd9b765f53f07a5c2e4b80c0e15c6c44047, 0x2b29fd644252cfa867688eb7bf755627b8984e6312ea36a7ce82c9d3c9d0e665]);
        vk.Z = Pairing.G2Point([0x5490f1553d46b72d5065d6f5871cba69cfd21a304ac6d51de223259f9790c50, 0x2c67c3dd4c22cc93e4fee9872297e280801b32f0c8435c1afaace0d6b8b90965], [0x2c242fef130aae1603754fe03ea501d79385afbfb1f70bdcf0eff7683859a6a, 0x2400f6464e0a2c32be4f0e0da5a701b7d13f78bb7b30e361f90140f664a99fb7]);
        vk.IC = new Pairing.G1Point[](5);
        vk.IC[0] = Pairing.G1Point(0x2ee4f10762b35f2a67ae89efebac135e4203cdc7b162f42d0a944ab8ba44a086, 0x2a7d46ff63646ba212c15001c58f4f9c4ecd433557c274fd7320eb824953b914);
        vk.IC[1] = Pairing.G1Point(0x2cfa9355b8bb1cdec908183814869029724b02e02d337e03916d9cb8a989d9f1, 0x164b565e3808c3d9868f1072ebe6b42c84ef340976fe1dbc6faa39ff3adfd3fc);
        vk.IC[2] = Pairing.G1Point(0x10b5e80161c4d707bc4e14f6c30b9c4420ec3cd52483c3226236f3ae6b055128, 0x28c978aeb361c6995ab5cd7d16db711fd06b89220cfdcf9c79a9254962ca1714);
        vk.IC[3] = Pairing.G1Point(0x294e0fe8a51402e49f309de676f367d8348dd5f7a6f78d10175ec0fa5f3b4a46, 0x2c24e6fda46bbe79237df7b02516fcfbc109fd0b9e1cc6b6fccd8c1bade31e90);
        vk.IC[4] = Pairing.G1Point(0x1bc44dac5f2d4a04b7e8221bb8ed82c371a7f850dc5c7896482eb1bdc1083996, 0x19bc80a310c0ca4fec41dda4be8e7d50bc51b773412f894e4f925b73b9534568);
    }
    function verify(uint[] input, Proof proof) internal returns (uint) {
        VerifyingKey memory vk = verifyingKey();
        require(input.length + 1 == vk.IC.length);
        // Compute the linear combination vk_x
        Pairing.G1Point memory vk_x = Pairing.G1Point(0, 0);
        for (uint i = 0; i < input.length; i++)
            vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.IC[i + 1], input[i]));
        vk_x = Pairing.addition(vk_x, vk.IC[0]);
        if (!Pairing.pairingProd2(proof.A, vk.A, Pairing.negate(proof.A_p), Pairing.P2())) return 1;
        if (!Pairing.pairingProd2(vk.B, proof.B, Pairing.negate(proof.B_p), Pairing.P2())) return 2;
        if (!Pairing.pairingProd2(proof.C, vk.C, Pairing.negate(proof.C_p), Pairing.P2())) return 3;
        if (!Pairing.pairingProd3(
            proof.K, vk.gamma,
            Pairing.negate(Pairing.addition(vk_x, Pairing.addition(proof.A, proof.C))), vk.gammaBeta2,
            Pairing.negate(vk.gammaBeta1), proof.B
        )) return 4;
        if (!Pairing.pairingProd3(
                Pairing.addition(vk_x, proof.A), proof.B,
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
        ) public returns (bool r) {
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
            emit Verified("Transaction successfully verified.");
            return true;
        } else {
            return false;
        }
    }
}
