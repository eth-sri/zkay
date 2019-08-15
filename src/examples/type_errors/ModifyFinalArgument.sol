pragma solidity ^0.5.0;

contract ModifyFinalArgument {

	function f(final uint x) {
		x = 10;
	}
}
