pragma solidity ^0.5.0;

contract MultipleReturnValues {

    uint ret;

    function replicate2(uint x) pure internal returns(uint, uint) {
        return (x+1, x+2);
    }

    function replicate3(uint x) pure internal returns(uint, uint, uint) {
        return (x, x+1, x+2);
    }

    function replicate_priv(uint y, uint@me z) pure internal returns(uint, uint@me) {
        return (y + (reveal(z > 20, all) ? 42 : 0), 2*z + y);
    }

    function replicate_circ(uint@me x) pure internal returns(uint@me, uint@me) {
        return (x + 42, x + 21);
    }

    function single_circ(uint@me x) pure internal returns (uint@me) {
        uint@me r1; uint@me r2;
        (r1, (x, r2)) = (x, replicate_circ(x));
        // r1 = x; r2 = x+21
        return r1 + r2; // ret = 2x+21  (2*(5+x) + 21)
    }

    function test(uint x) public {
        uint a1; uint a2; uint a3;
        (a1, a2, a3) = replicate3(x);
        (a1, (a2, a3)) = (x, replicate2(x)); // a1 = x, a2 = x + 1, a3 = x + 2
        uint@me k = 5; // k = 5
        uint@me p; // p = 0
        (k, p) = true ? (reveal(5, me), reveal(0, me)) : (k, p);
        (k, p) = (p, k);
        (k, p) = (p, k);
        require(reveal(k + p + a1 == 5+x, all));
        require(reveal(k * (a2 + a3) == 10*x + 15, all));
        require(reveal(single_circ(k + p + a1) == 2*x + 31, all));
        k = single_circ(k + p + a1) + k * (a2 + a3);
        require(reveal(k == 12*x + 46, all));
        (a1, k) = replicate_priv(42, k);
        ret = reveal(k, all); // ret = 2*k + 42 = 24*x + 92 + 42 = 24*x + 134
    }
}
