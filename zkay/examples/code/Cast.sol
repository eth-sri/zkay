pragma solidity ^0.5.0;

contract Cast {
	enum test {v1, v2, v3}
	enum test2 {
		t1, t2,
		t3
	}

	uint8 res;
	uint8 res2;
	function f(uint a) public {
		test x = test.v3;
		uint y = uint(x);
		test v = test(y);
		uint32 k = uint32(y) + uint16(a);
		bool@me b = (uint8(a) + a) != 0;
		int64@me p = int64(b ? uint32(x) : k + y + (b ? 1 : 0));
		int32@me secint = int32(p + int64(x));
		int8@me secint8 = 127;

		address@me priv_addr = me;
		priv_addr = b ? priv_addr : address(uint(block.coinbase) + uint32(secint));
		address unsealed_addr = reveal(priv_addr, all);

		test@me priv_enum = x;
		priv_enum = b ? priv_enum : test(uint(v)+1);
		test unsealed_enum = reveal(priv_enum, all);

		res = reveal(uint8(p), all);
		res2 = uint8(reveal(p, all));
	}
}

