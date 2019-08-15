pragma solidity ^0.5.0;

contract Ite {

	uint@all x;

	function f(bool@all a, uint@all b, uint@all c) public{
		x = a ? b : c;
	}
}
