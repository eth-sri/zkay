pragma solidity ^0.5.0;

contract shortcirc {
    uint x1;
    uint x2;
    bool res;

    mapping (uint => uint) smap;

    function priv1(uint@me val) public returns(bool) {
        x1 = reveal(val, all);
        return reveal(val > 50, all);
    }

    function priv2(uint@me val) public returns(uint) {
        x2 = reveal(val, all);
        return reveal(val * 2, all);
    }

    function priv3(uint val) public returns(uint@me) {
        x2 = val * 2;
        return val * 3;
    }

    function test_short() public {
        uint@me v = 51;
        uint@me v2 = 123;
        uint@me v3 = 14;
        uint@me v4 = 70;
        res = priv1(v) && priv1(v2) ? priv1(v3) : priv1(v4);

        v = 2;
        // smap[6] (x2 == 2) = 140 (x2 == 70) > 28 (x2 == 14) ? 84 (x2 == 42) + 84 (x2 == 42)
        smap[x2 + priv2(v) + x2] = priv2(v4) > priv2(v3) ? priv2(priv3(x2)) + priv2(x2) : priv2(x2) - priv2(v);
        // smap[6] = 168, x2 == 42
    }
}
