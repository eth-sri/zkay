pragma solidity ^0.5.0;

contract PrivateForArgument {
    mapping(address!x => uint@x) values;

    function set(final address a, uint x) public {
        uint@a v = x;
        values[a] = v;
    }

}

