pragma solidity ^0.5.0;

contract shortcirc {
    uint x1;
    uint x2;
    bool res;

    mapping (uint => uint) smap;

    final address owner;
    uint@owner secval;
    uint pubval;
    constructor() public {
        owner = msg.sender;
    }

    function priv1(uint@me val) internal returns(bool) {
        x1 = reveal(val, all);
        return reveal(val > 50, all);
    }

    function priv2(uint@me val) internal returns(uint) {
        x2 = reveal(val, all);
        return reveal(val * 2, all);
    }

    function priv22(uint@me val) internal returns(uint) {
        x1 = reveal(val, all);
        return reveal(val * 3, all);
    }

    function priv3(uint val) internal returns(uint@me) {
        x2 = val * 2;
        return val * 3;
    }

    function priv4(uint val) internal returns(uint) {
        require(owner == me);
        secval = secval + val;
        pubval = reveal(secval + 42, all);
        return 0;
    }

    function test_short_1(bool v, uint val) public {
        uint x = v ? 1 : priv4(val);
        res = x != 0;
    }

    function blub() public returns(bool) {
        return true && true;
    }

    function test_short() public {
        uint@me v = 51;
        uint@me v2 = 123;
        uint@me v3 = 14;
        uint@me v4 = 70;
        res = priv1(v) && priv1(v2) ? priv1(v3) : priv1(v4);

        v = 2;
        uint idx = x2;
        // idx = 0
        idx = idx + priv2(v) + priv22(v);
        // x2 == 2, x1 == 2, idx = 0 + 4 + 6 = 10
        smap[idx] = priv2(v4) > priv22(v3) ? priv2(priv3(x2)) : priv2(x2) - priv22(v);
        // x2 = 70, x1 = 14, 140 > 42
        // x2 = 140, priv3 = 210
        // x2 = 210, priv2 = 420
        // smap[10] = 420, x1 = 14, x2 == 210
    }
}
