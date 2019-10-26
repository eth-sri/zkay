pragma solidity ^0.5.0;

contract ModifyFinalStateVar {

	final uint@all x;

	constructor() public{
	    x = 0;
	}

	function f() {
		x = 10;
	}
}
