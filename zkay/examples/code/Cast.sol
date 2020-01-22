pragma solidity ^0.5.0;

contract Cast {
	enum test {v1, v2, v3}
	enum test2 {
		t1, t2,
		t3
	}

	final address owner;
	int64@owner p;
	uint8 res;
	test@owner sealed_enum;
	address@owner priv_addr;

	int248@owner negval;
	int248@owner nv2;
	int8 pv2;
	uint248 pv3;
	uint248 pv4;

	constructor() public {
		owner = me;
	}

	function f(uint a) public {
		require(owner == me);

		test x = test.v3;
		bool@me b;
		{
			uint y = uint(x);
			test v = test(y);
			uint32 k = uint32(y) + uint16(a);                        // k = uint16(a) + 2
			b = (uint8(a) + a) > 500;                                // b = (uint8(a) + a) > 500
			p = int64(b ? uint32(x) : k + y + (b ? 1 : 0));          // p = int64(b ? (2) : (k + 2))

			test@me priv_enum = x;
			sealed_enum = b ? priv_enum : test(uint(v)-1);           // priv_enum = b ? test.v3 : test.v2
		}
		int32@me secint = int32(p + int64(x));                       // secint = int32(p + 2)
		int8@me secint8 = 127;                                       // secint8 = 127

		priv_addr = me;
		priv_addr = b ? priv_addr : address(42 + uint32(secint));    // priv_addr = b ? me : 42 + uint32(secint)
		address unsealed_addr = reveal(priv_addr, all);              // unsealed_addr = priv_addr
		require(reveal(unsealed_addr == priv_addr, all));

		test unsealed_enum = reveal(sealed_enum, all);               // unsealed_enum = priv_enum
		require(reveal(unsealed_enum == sealed_enum, all));

		res = reveal(uint8(p), all);                                 // res = res2 = uint8(int64(b ? (2) : (k + 2)))
		uint res2 = uint8(reveal(p, all));
		require(res == res2);
	}

	function test_signed_casts() public {
		require(owner == me);
		negval = -1;
		require(reveal(negval, all) == -1);
		require(reveal(negval == -1, all));
		nv2 = -negval;
		require(reveal(nv2, all) == 1 && reveal(-nv2 == negval, all));
		require(reveal(uint248(negval) == (2**248 - 1), all));
		pv2 = int8(reveal(negval, all));
		pv3 = reveal(uint248(negval), all);
		pv4 = uint248(reveal(negval, all));

		uint248@me intmin = 2 ** 247;
		require(reveal(int248(intmin) == -int248(intmin), all));
		require(-reveal(intmin, all) == 2 ** 247);

		uint8@me val = 10;
		int8 m5 = -5;
		require(reveal(int8(val) - 15, all) == m5);
		require(reveal(int8(val - 15), all) == m5);

		int8@me m1 = -1;
		require(reveal(m1 == -1, all));
	}
}
