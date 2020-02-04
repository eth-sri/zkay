pragma solidity ^0.5.0;

contract NestedPrivateIfCond {
    final address owner;

    bool@owner val;
    uint@owner res;

    mapping (address!x => uint@x) map;

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
                x = 5;
                {
                    x = 42;
                    uint x;
                    {
                        x = 3;
                        uint x = 5;
                    }
                }
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

    function doit() pure internal returns(uint) {
        //res = 12;
        return 1;
    }

    function test_map(uint@me z) public {
        uint@me v;
        if (z > 2) {
            v = 10 + doit();
            //map[me] = 10;
        }
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

        uint res;
        {
            res = 2;
            uint res = 6;
            require(res == 6);
        }
        res = 7;
        {
            uint res = 27;
            require(res == 27);
        }
        require(res == 7);
    }
}
