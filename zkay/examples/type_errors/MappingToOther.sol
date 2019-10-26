pragma solidity ^0.5.0;

contract MappingToOther {

    mapping(address!x => uint@x) values;


	function f(address a, uint@me value) {
		values[a] = value;
	}

}
