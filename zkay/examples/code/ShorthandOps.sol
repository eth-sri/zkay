pragma solidity ^0.5.0;

contract ShorthandOps {
	uint@all x;

	function f(uint a, uint@me b) public {
		uint k = a;
		uint origb = reveal(b, all);
		a++;
		++b;
		require(reveal(b - 1, all) == origb);
		uint@me b2 = b;
		b--;
		b -= 1;
		b += 1;
		b++;
		require(reveal(b == b2, all));
		a -= 1;
		a *= 1;
		require(k == a);
		if (a < 100) {
			a <<= 1;
			require(k*2 == a);
		}

		int8@me b3 = -1;
		require(reveal(b3 == (b3 >> 1), all));
		require(reveal((b3 << 1) < b3, all));

		uint32@me v = 0xff;
		require(reveal(v ^ v == 0, all));
		require(reveal(v & 0xf == 0xf, all));
		require(reveal(v ^ 0xffff == 0xff00, all));
		require(reveal(v | 0xffff == 0xffff, all));
		require(reveal(~v == 0xffffff00, all));

		a &= (0xf | a);
		a ^= 20;
		a |= 123;
	}
}

