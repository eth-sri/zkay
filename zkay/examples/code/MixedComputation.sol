pragma solidity ^0.5.0;

contract MixedComputation {
    final address master;
    uint a = 1;
    uint b = 1;
    uint@master x;
    uint@master y;

    constructor() public{
        master = me;
        x = 2;
        y = 0;
    }

    function f() public{
        require(me == master);
        b = 18 * a - 1;
        a = reveal(((12 + 8)*x - (a % 3)*y) + (a * b), all);
        x = x + 1;
        x = (a / 2) * x;
        a = 3 + reveal(x - 2, all);
    }
}