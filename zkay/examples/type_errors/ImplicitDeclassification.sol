pragma solidity ^0.5.0;

contract ImplicitDeclassification {

    address owner;

    uint@owner a;
    uint@all b;

	function f() public {
	    require(owner == me);
		b = a;
	}
}
