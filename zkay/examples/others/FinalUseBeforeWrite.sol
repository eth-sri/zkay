pragma solidity ^0.5.0;

contract FinalUseBeforeWrite {

    final address owner;
    final uint@owner value;

    constructor(uint@me v) public {
        require(owner == me);
        // owner is not set yet, but `value` is owned by it
        value = v;
        owner = me;
    }

}
