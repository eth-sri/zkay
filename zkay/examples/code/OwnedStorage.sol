pragma solidity ^0.5.0;

// simple getter/setter contract
contract OwnedStorage {
    final address@all owner;
    uint@owner storedData;

    constructor() public{
        owner = me;
    }

    function set(uint@me x) public {
        require(me == owner);
        storedData = x;
    }

    function get() public returns (uint@owner) {
        return storedData;
    }
}

