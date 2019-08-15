pragma solidity ^0.5.0;

// Description: Simple multi-party computation
// Domain: Security
contract SumRing {
    uint result;
    final address master;
    uint@master masterSeed;
    mapping(address!x => uint@x) recVal;

    constructor(uint@me seed) public {
        master = me;
        masterSeed = seed;
        recVal[me] = seed;
    }

    function addVal(uint@me val, address next) public {
        recVal[next] = reveal(recVal[me] + val, next);
    }

    function evaluateSum() public {
        require(me == master);
        result = reveal(recVal[me] - masterSeed, all);
    }
}