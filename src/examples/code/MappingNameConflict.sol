pragma solidity ^0.5.0;

contract MappingNameConflict {
    uint x;
    mapping(address!x => uint@x) values;
}
