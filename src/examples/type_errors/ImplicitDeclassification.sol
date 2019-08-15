pragma solidity ^0.5.0;

contract ImplicitDeclassification {

    address owner;

    uint@owner a;
    uint@all b;

	function f() {
	    require(owner == me);
		b = a;
	}
}
