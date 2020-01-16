pragma solidity ^0.5.0;

contract Cast {
	enum test {v1, v2, v3}
	enum test2 {
		t1, t2,
		t3
	}

	function f(uint a) public {
		test x = test.v3;
		uint y = uint(x);
		test v = test(y);
		uint32 k = uint32(y) + uint16(a);
		int p = int64(x);
	}
}

