pragma solidity ^0.5.0;

contract ifcond {
    final address owner;

    bool@owner val;
    uint@owner res;
    uint res2;

    constructor() public {
        owner = msg.sender;
    }

    function set_res(uint@me val) internal {
        require(owner == me);
        res = val;
    }

    function test_if(uint@me x) public {
        require(owner == me);

        val = reveal(x > 42, all);
        bool val2 = reveal(x > 50, all);
        if (reveal(val && x > 50, all) && val2) {
            set_res(1);
        } else {
            if (reveal(x > 10, all)) {
                set_res(2);
            } else {
                set_res(3);
            }
        }

        require(owner == me);
        res2 = reveal(res * 5, all);
    }
}
