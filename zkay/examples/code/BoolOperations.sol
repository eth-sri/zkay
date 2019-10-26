pragma solidity ^0.5.0;

contract BoolOperations {
    function f(uint@me a, uint@me b) public {
        bool c;
        c = reveal((a > b) || (a == b), all);
        c = reveal((a > b) && (a == b), all);
        c = reveal(!(a > b), all);
    }

}
