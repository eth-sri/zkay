pragma solidity ^0.5.0;

contract Indexing_Nested {

    mapping(address!x => mapping(address => uint@x)) values;


	function f(address a, uint@me value) {
		values[a][me] = value;
	}

}
