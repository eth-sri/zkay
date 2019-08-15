pragma solidity ^0.5.0;

contract ModifyFinalArgumentInConstructor {

	constructor() {
		final uint x = 10;
		x = 20;
	}
}
