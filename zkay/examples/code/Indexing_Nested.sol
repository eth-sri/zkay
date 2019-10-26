pragma solidity ^0.5.0;

contract Indexing_Nested {

    mapping(address!x => mapping(address!y => uint@x)) storage1;
    mapping(address!x => mapping(address!y => uint@y)) storage2;


	function f(address a, uint@me value) public{
		storage1[me][a] = value;
		storage2[a][me] = value;
	}

}
