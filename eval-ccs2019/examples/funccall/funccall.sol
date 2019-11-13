pragma solidity ^0.5.0;

contract funccall {
    final address owner;
    uint@owner res;
    uint pubval;

    constructor() public {
        owner = msg.sender;
    }

    function update_pubval() public {
        pubval = pubval + 1;
    }

    function some_comp(uint@me v1, uint@me v2) pure public returns (uint@me) {
        return v1 + v2;
    }

    function some_comp_pub(uint@me v1, uint@me v2) pure public returns (uint) {
        return reveal(v1 + v2, all);
    }

    function calc(uint@me v) public {
        require(owner == me);
        pubval = 0;
        res = v + some_comp(v, v);
        update_pubval();
        pubval = some_comp_pub(pubval, res);
    }
}
