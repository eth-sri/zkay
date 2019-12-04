pragma solidity ^0.5.0;

contract ControlFlow {

	uint@all x;

	function f(uint@all a, uint@me b) public {
		if (b > 0){
			x = a;
		}
	}
}

