================================
Language Overview
================================

In general, zkay can be regarded as a subset of Solidity with a few additional features and some minor differences.

--------------------------
Features specific to zkay
--------------------------

Final Variables
================

.. code-block:: zkay

	final uint x;

State variables can be declared final, which means that they can only be assigned once in the constructor.

Ownership
===========

Any primitive type variable can be turned into a *private* variable by annotating it with an optional ownership label using the syntax:

.. code-block:: zkay

	type@owner identifier;

Which ownership labels are available depends on the scope:
- local variables: any final or constant address state variable, as well as the special value *me* (which corresponds to the address of msg.sender) can be used as an ownership label
- state variables: only final or constant state variables are allowed
- function parameters: only *me* is allowed
- function return parameters: in general only *me*, for private/internal functions also any final or constant state address variable

It is also possible to declare mappings where the privacy annotation of a value depends on the key:

.. code-block:: zkay

	mapping(address!x => uint@x) private_values;

Private variables are **always encrypted** on the the chain such that they can only be read by the designated owner.

Reclassification
================

If the transaction issuer owns a variable, it is possible to reveal its value to another owner or to make a private value public.

.. code-block:: zkay

	uint@me x;
	uint@bob x_bob; x_bob = reveal(x, bob);
	uint x_public = reveal(x, all)

Revealing to *all* will decrypt the value and publish the plaintext, whereas revealing to another owner will reencrypt the value for the new owner.

When assigning a public value to a private variable, zkay implicitly classifies the value, i.e.:

.. code-block:: zkay

	uint@me x = 5; // <=> uint@me x = reveal(5, me)

Private Computations
====================

One of zkay's most powerful features is the ability to express computations over private values.

Any variable for which the compiler can statically prove that the ownership label is equivalent to *@me* can be used within an expression. e.g.:

.. code-block:: zkay

	uint@me val;
	uint@me res = 2 * val + 5;

Mere assignment is also possible for values which are not owned by `msg.sender`, as this does not require decryption e.g.:

.. code-block:: zkay

	uint@owner x;
	uint@owner y;
	x = y;

Limitations
------------

- Private expressions are not allowed within loops or recursive functions (and vice versa).
- Private expressions must not contain side effects.
- If the condition of an if statement is a private expression, then the only allowed side-effects within the branches are assignments to primitive-type variables owned by *@me*.
- Private bitwise operations cannot be used with 256-bit types.
- When bit-shifting private values, the shift amount needs to be a constant literal.
- Address members (balance, send, transfer) are not accessible on private addresses.
- Division and exponentiation oeprators are not supported within private expressions.

Warning
------------
- Private 256-bit values overflow at a large prime (~253.5 bits).
- | Comparison of private 256-bit values >= 2^252 may fail.
  | **!!! If you cannot guarantee that the operands of a comparison stay below that threshold (i.e. if the values are freely controllable by untrusted users), use a smaller integer type to preserve correctness !!!**

This does only apply to 256-bit values and is due to internal zk-SNARK circuit limitations. Smaller types are not affected.

--------------------------
General Language Features
--------------------------

Contract Structure
==================

Types
================

The following primitive types are supported in zkay:

- bool
- int, int8, ..., int256 (int256 only public)
- uint, uint8, ..., uint256
- enums
- address
- address payable

Additionally, zkay also supports the mapping type (only as state variable).
Other reference types are currently not supported.

Statements
================

Expressions
================

Cryptocurrency Globals
=======================

