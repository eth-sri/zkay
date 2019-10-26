pragma solidity ^0.5.0;

contract Eq {

	uint@all x;

	function f(uint@all a, uint@all b) public{
		if (a == b) {
		    x = a;
		}
	}
}

