
pragma solidity ^0.5.0;

import "AddFunction.sol";

contract AddUser {

    AddFunction a;

    constructor(AddFunction a_) public{
        a = a_;
    }

    function f(uint x, uint y) view public returns (uint) {
        return a.myadd(x,y);
    }

}
