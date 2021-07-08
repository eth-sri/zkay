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

Private variables are encrypted on the blockchain such that they can only be read by the designated owner. Which ownership labels are available depends on the scope:

- local variables: any final or constant address state variable, as well as the special value *me* (which corresponds to the address of msg.sender) can be used as an ownership label
- state variables: only final or constant state variables are allowed
- function parameters: only *me* is allowed
- function return parameters: in general only *me*, for private/internal functions also any final or constant state address variable

If a variable is declared private to *me*, it is called *self-owned*.

It is also possible to declare mappings where the privacy annotation of a value depends on the key. In the following example, the entry :code:`private_values[alice]` is owned by :code:`alice`:

.. code-block:: zkay

    mapping(address!x => uint@x) private_values;


Reclassification
================

To prevent implicit information leaks, private expressions cannot be assigned to a different owner. However, you can explicitly reveal a self-owned expression to a different address, or to the public (using the dedicated :code:`all` owner):

.. code-block:: zkay

    uint@me x;
    uint@bob x_bob;
    x_bob = reveal(x, bob);
    uint x_public = reveal(x, all);

Revealing to *all* will decrypt the value, whereas revealing to another owner will re-encrypt the value for the new owner.

It is possible to implicitly make a public expression private. For example:

.. code-block:: zkay

    uint@me x = 5; // <=> uint@me x = reveal(5, me)

Private Computation on Self-owned Variables
===========================================

Many operations in zkay can be evaluated on expressions where all variables are self-owned (owner *me*). This allows performing computation on private data. For example:

.. code-block:: zkay

    uint@me val;
    uint@me res = 2 * val + 5;

Sometimes, the owner of a variable is syntactically different from *me*, but is guaranteed to evaluate to the caller address at runtime. In the example below, zkay detects that the variable a is actually self-owned.

.. code-block:: zkay

    uint@alice a;
    uint@me x;
    require(me == alice);
    x = a + x;

Limitations
------------

- Private expressions are not allowed within loops or recursive functions (and vice versa).
- Private expressions must not contain side effects.
- If the condition of an if statement is a private expression, then the only allowed side-effects within the branches are assignments to primitive-type variables owned by *me*.
- Private bitwise operations cannot be used with 256-bit types.
- When bit-shifting private values, the shift amount needs to be a constant literal.
- Address members (balance, send, transfer) are not accessible on private addresses.
- Division, modulo and exponentiation oeprators are not supported within private expressions.

Warning
------------
- Private 256-bit values overflow at a large prime (~253.5 bits).
- | Comparison of private 256-bit values >= 2^252 may fail.
  | **If you cannot guarantee that the operands of a comparison stay below that threshold (i.e. if the values are freely controllable by untrusted users), use a smaller integer type to preserve correctness.** This does only apply to 256-bit values and is due to internal zk-SNARK circuit limitations. Smaller types are not affected.

Private Computation on Foreign Variables
========================================

Homomorphism Tags
-----------------

Using :code:`<+>`, a variable can be declared to allow addition-based modifications by other parties (see below). Such variables will be encrypted using an additively homomorphic encryption scheme. Due to limitations imposed by the encryption scheme, these variables must be unsigned integers of at most 32 bits. For example, we can declare:

.. code-block:: zkay

    uint32@alice<+> x;

Foreign Addition and Subtraction
--------------------------------

Relying on homomorphic encryption, zkay allows performing addition and subtraction operations on variables owned by an account other than *me*, provided the variables are declared with :code:`<+>`. For example:

.. code-block:: zkay

    uint32@alice<+> val;
    val = val + 1;
    val = val - 1;

Mixing two different non-public owners is not allowed, so the following is rejected by zkay:

.. code-block:: zkay

    uint32@alice<+> a;
    uint32@bob<+> b;
    a = a + b;          // ! type error

Foreign Multiplication
----------------------

Zkay also allows multiplying foreign values by constant scalars, or by values which are owned by *me* and immediately revealed to the other party. For example:

.. code-block:: zkay

    uint32@me x;
    uint32@alice<+> val;
    val = val * 2;
    val = val * reveal(x, alice);

Switching Tags
--------------

Zkay can automatically switch between homomorphism tags of self-owned expressions. For the following code snippet, zkay would automatically re-encrypt the value of x using a non-homomorphic encryption scheme before storing the result into y:

.. code-block:: zkay

    uint32@me x;
    uint32@me<+> y;
    y = x;

Typically, zkay can automatically figure out where to introduce such a switch of encryption schemes. However, if this fails, you may always explicitly instruct zkay to change the homomorphism tag of a self-owned expression using the *unhom* and *addhom* expressions exemplified below:

.. code-block:: zkay

    uint32@me x;
    uint32@me<+> y;
    y = addhom(x);
    x = unhom(y);


Warning
------------
The result of a homomorphic addition or multiplication may overflow the 32 bit length restriction of the encryption scheme. Similarly, the result of a homomorphic subtraction may underflow below 0. In these cases, decryption of the variable will fail in zkay. **The contract is expected to contain application-specific logic ensuring these over- and underflows cannot happen.**

--------------------------
General Language Features
--------------------------

Contract Structure
==================

A zkay contract is of the following shape:

.. code-block:: zkay

    pragma zkay ^0.2.0; // Pragma directive with version constraint

    // For now, import statements are not supported

    // Example contract defintion
    contract Test {
        // Example enum definition
        enum TestEnum {
            A, B, C
        }

        // Example state variable declarations
        final address owner;
        uint@owner value;
        TestEnum e_value;

        // Optional constructor definition
        constructor() public {
            owner = me;
        }

        // Example function definition
        function set_value(uint@me _value) public returns(uint) {
            require(owner == me);
            require(!is_five());
            value = _value;
            return reveal(_value, all);
        }

        // Example internal function
        function is_five() internal view returns(bool) {
            require(owner == me);
            return reveal(value == 5, all);
        }
    }

Types
================

The following primitive types are fully supported in zkay:

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

.. code-block:: zkay

    function test() public returns(uint) {
        // Declaration & Assignment
        uint x = 3;
        uint@me y = 5;

        // Require assertions
        require(x == 3);

        // Public loops
        for (uint i = 0; i < 5; ++i) {
            x += 1;
        }
        uint i = 0;
        while(i < 5) {
            i++;
            break;
        }
        do {
            i++;
        } while (i < 5);

        // If statements
        if (x == 3) {
            if (y < 3) { // With private condition
                y = priv_f(2); // Private function calls
            }
        }

        // Function calls
        test2(3, 4);

        // !! Return statement must always come at the end of the function body in zkay !!
        return x;
    }

    function priv_f(uint x) pure internal returns(uint@me) { return x; /* ... */ }

    function test2(uint x, uint@me x2) public { /* ... */ }


Expressions
================

zkay supports largely the same operators as Solidity, with the same precedence rules.

Tuples also work the same way as in Solidity.

**Note**: In contrast to Solidity, zkay does not have assignment expressions. Function calls are the only expressions which may have side-effects.

Cryptocurrency
=======================

Public functions can be declared `payable` to receive ether.

There is some limited support for the `now`, `block`, `tx` and `msg` globals (all fields with `bytes` types are unavailable).

You can use the `transfer` member function on public address payable variables to transfer funds.
