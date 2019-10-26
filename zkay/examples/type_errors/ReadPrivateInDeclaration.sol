pragma solidity ^0.5.0;

contract ReadPrivateInDeclaration {
    final address master;
    uint@master count;

    constructor() public {
        master = me;
        count = 0;
    }

    function test() public {
        uint c = count;
    }
}
