pragma solidity ^0.5.0;

contract NestedPrivateIfCond {
    final address owner;

    bool@owner val;
    uint@owner res;

    constructor() public {
        owner = msg.sender;
    }


    function priv_if(uint@me v, uint@me v2) view internal returns(uint@me) {
        uint@me ret;
        uint@me hans;
        if (v > v2) {
            uint@me x = 42;
            if (v2 + v < 100) {
                x = 2;
                ret = 14;
            } else {
                x = 42;
                ret = v - v2 + x - 42;
                hans = 42;
            }
            v = v2;
        } else if (v < v2) {
            ret = v * v2 + 5;
            v = v2;
        } else {
            ret = v2;
            v = v2;
        }
        return ret + reveal(v - v2, all);
    }

    function test_if_outer(uint@me x) public {
        require(owner == me);
        val = x == 42;
        if (x < 100) {
            res = x + 1 > 42 ? priv_if(x, x) : priv_if(x > 0 && val ? 2*x : 3*x, 2*x + 5);
        } else {
            res = x - 100;
        }
    }

    function test_if(uint@me x) public {
        require(owner == me);
        val = x == 42;
        if (reveal(x < 100, all)) {
            res = x + 1 > 42 ? priv_if(x, x) : priv_if(x > 0 && val ? 2*x : 3*x, 2*x + 5);
        } else {
            res = x - 100;
        }
    }
}
