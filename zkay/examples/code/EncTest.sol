pragma solidity ^0.5.0;

contract EncTest {
    final address owner;
    uint@owner v;

    constructor() public {
        owner = msg.sender;
    }

    function test(uint@me val) public {
        require(owner == me);
        v = v + val + 2;
    }
}
