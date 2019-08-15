pragma solidity ^0.5.0;

contract ReclassGeq {

    function f(uint@me a, uint@me b) public {
        bool c;
        c = reveal(a >= b, all);
    }
}
