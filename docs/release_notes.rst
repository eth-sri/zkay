Release Notes
================================

v0.3.0 (2022-03-21)
--------------------

- Introduced homomorphic encryption schemes (Paillier, ElGamal)
- Support for operations on foreign values: addition, subtraction, and scalar multiplication by public or self-owned scalars

v0.2.0 (2020-09-01)
--------------------

- Support for real encryption (RSA, ECDH+Chaskey, ECDH+AES)
- Fully automatic transaction transformation (interactive shell for issuing zkay transactions)
- Many new language features

  * Function calls
  * Private if statements
  * Cryptocurrency features
  * Public loops
  * Multiple return values
  * Extended primitive type support (int/uint + variants, Enums, address/address payable etc.)
  * Correct overflow handling
  * bitwise and shift operators

- Improved Architecture (higher modularity)
- Up to 10x better compilation performance
- Greatly improved user experience (configuration file support, easy contract packaging, nice error messages, ...)


v0.1.0 (2019-09-20)
--------------------

Original proof of concept release for CCS2019.
See `publication <https://www.sri.inf.ethz.ch/publications/steffen2019zkay>`_.
