pragma solidity ^0.5.0;

contract NestedPrivateIfCond {
    final address owner;

    bool@owner val;
    uint@owner res;
    uint res2;

    constructor() public {
        owner = msg.sender;
    }

    function set_res(uint@me val) internal {
        require(owner == me);
        res = val + 1;
    }

    function priv_if(uint@me v, uint@me v2) view internal returns(uint@me) {
        uint@me ret;
        if (v > v2) {
            uint x = 42;
            if (v2 + v < 100) {
                ret = 14;
            } else {
                ret = v - v2;
            }
        } else if (v < v2) {
            ret = v * v2 + 5;
        } else {
            ret = v2;
        }
        return ret;
    }

    function test_if(uint@me x) public {
        require(owner == me);
        val = x == 42;
        if (reveal(x < 100, all)) {
            res = x + 1 > 42 ? priv_if(x, x) : priv_if(x > 0 && val ? 2*x : 3*x, 4*x);
        } else {
            res = x - 100;
        }
    }
}
