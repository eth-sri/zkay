pragma solidity ^0.5.0;

contract BoolNegation {
    function f() public {
        bool b;
        b = true;
        b = !b;
    }
}
