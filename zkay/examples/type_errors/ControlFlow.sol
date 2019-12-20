pragma solidity ^0.5.0;

contract ControlFlow {
	final address owner;

	uint@all x;
	uint@owner c;

	function f(uint@all a, uint@me b) public {
		if (b > 0){
			if (c < 42) {
				x = a;
			}
		}
	}
}

