pragma solidity ^0.5.0;

contract Indexing_Nested {

    mapping(address => mapping(address!y => uint@y)) values;


	function f(address a, uint@me value) {
		values[me][a] = value;
	}

}
