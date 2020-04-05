pragma solidity ^0.5.0;

contract Analysis {
	address@all x1;
	address@all x2;
	address@all x3;
	address@all x4;
	address@all x5;

	function f1() public
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	{

		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		require(x1 == x2);
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]


		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		x3 = x4;
		// [['all'], ['me'], ['x1', 'x2'], ['x3', 'x4'], ['x5']]


		// [['all'], ['me'], ['x1', 'x2'], ['x3', 'x4'], ['x5']]
		x3 = x3;
		// [['all'], ['me'], ['x1', 'x2'], ['x3', 'x4'], ['x5']]
	}
	// [['all'], ['me'], ['x1', 'x2'], ['x3', 'x4'], ['x5']]

	function f2() public
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	{

		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		require(x1 == x2);
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]


		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		require(x2 == x3);
		// [['all'], ['me'], ['x1', 'x2', 'x3'], ['x4'], ['x5']]


		// [['all'], ['me'], ['x1', 'x2', 'x3'], ['x4'], ['x5']]
		x3 = x4;
		// [['all'], ['me'], ['x1', 'x2'], ['x3', 'x4'], ['x5']]
	}
	// [['all'], ['me'], ['x1', 'x2'], ['x3', 'x4'], ['x5']]

	function f3() public
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	{

		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		x1 = x2;
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]


		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		if (true)
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		{

			// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
			x3 = x4;
			// [['all'], ['me'], ['x1', 'x2'], ['x3', 'x4'], ['x5']]
		}
		// [['all'], ['me'], ['x1', 'x2'], ['x3', 'x4'], ['x5']]
		 else
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		{

			// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
			x4 = x5;
			// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4', 'x5']]
		}
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4', 'x5']]
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]


		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		require(x2 == x3);
		// [['all'], ['me'], ['x1', 'x2', 'x3'], ['x4'], ['x5']]
	}
	// [['all'], ['me'], ['x1', 'x2', 'x3'], ['x4'], ['x5']]

	function f3plus() public
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	{

		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		x1 = x2;
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]


		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		if ((x1 == x3 && !(x4 != x5 || x1 != x4)))
		// [['all'], ['me'], ['x1', 'x2', 'x3', 'x4', 'x5']]
		{

			// [['all'], ['me'], ['x1', 'x2', 'x3', 'x4', 'x5']]
			x2 = me;
			// [['all'], ['me', 'x2'], ['x1', 'x3', 'x4', 'x5']]
		}
		// [['all'], ['me', 'x2'], ['x1', 'x3', 'x4', 'x5']]
		 else
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		{

			// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
			require(x1 == me);
			// [['all'], ['me', 'x1', 'x2'], ['x3'], ['x4'], ['x5']]


			// [['all'], ['me', 'x1', 'x2'], ['x3'], ['x4'], ['x5']]
			x4 = x5;
			// [['all'], ['me', 'x1', 'x2'], ['x3'], ['x4', 'x5']]
		}
		// [['all'], ['me', 'x1', 'x2'], ['x3'], ['x4', 'x5']]
		// [['all'], ['me', 'x2'], ['x1'], ['x3'], ['x4', 'x5']]


		// [['all'], ['me', 'x2'], ['x1'], ['x3'], ['x4', 'x5']]
		require(x2 == x3);
		// [['all'], ['me', 'x2', 'x3'], ['x1'], ['x4', 'x5']]
	}
	// [['all'], ['me', 'x2', 'x3'], ['x1'], ['x4', 'x5']]

	function f3for() public
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	{

		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		require(x4 == x5);
		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4', 'x5']]


		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		for (
		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4', 'x5']]
		x1 = x2;
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4', 'x5']]
		 x2 == x3;)
		// [['all'], ['me'], ['x1'], ['x2', 'x3'], ['x4'], ['x5']]
		{

			// [['all'], ['me'], ['x1'], ['x2', 'x3'], ['x4'], ['x5']]
			x2 = x4;
			// [['all'], ['me'], ['x1'], ['x2', 'x4'], ['x3'], ['x5']]


			// [['all'], ['me'], ['x1'], ['x2', 'x4'], ['x3'], ['x5']]
			x2 = x1;
			// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		}
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
	}
	// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]

	function f4() public
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	{

		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		x1 = x2;
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
	}
	// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]

	function f5() public
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	{

		// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		x1 = x2;
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]


		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
		{

			// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5'], ['y']]
			address y = x3;
			// [['all'], ['me'], ['x1', 'x2'], ['x3', 'y'], ['x4'], ['x5']]
		}
		// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]
	}
	// [['all'], ['me'], ['x1', 'x2'], ['x3'], ['x4'], ['x5']]

	function f6() public
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	{

		// [['all'], ['me'], ['x'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		uint x;
		// [['all'], ['me'], ['x'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]


		// [['all'], ['me'], ['x'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
		x = 1234;
		// [['all'], ['me'], ['x'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
	}
	// [['all'], ['me'], ['x1'], ['x2'], ['x3'], ['x4'], ['x5']]
}