# Implementation Notes: Homomorphic Encryption in v0.3

This file gives an overview of where the various homomorphic features of zkay v0.3 are implemented. The changes compared to v0.2 are grouped by subsystem, see Fig. 2 (p. 12) of the [zkay 0.2 technical report](https://arxiv.org/pdf/2009.01020.pdf).

## Parsing

We support non-homomorphic `T@A<>` and additively homomorphic types `T@A<+>`. Other homomorphic types are possible, but only non-homomorphic and additively homomorphic types have been implemented so far. Further, we add two new keywords, `addhom` and `unhom`, to convert between non-homomorphic and homomorphic types.

**Relevant code**:
- [zkay/solidity_parser/Solidity.g4](zkay/solidity_parser/Solidity.g4): Syntax for homomorphic type names. See `homomorphismAnnotation` for `<>` / `<+>` tags. After making changes, make sure that antlr 4.8 or newer is installed, then run [solidity_parser/Makefile](zkay/solidity_parser/Makefile).
- [zkay/compiler/solidity/fake_solidity_generator.py](zkay/compiler/solidity/fake_solidity_generator.py): Extended the RegEx that turns private zkay code into fake public Solidity code to also remove `addhom` / `unhom` (we piggy-back on the Solidity compiler for basic type checking).
- [zkay/zkay_ast/build_ast.py](zkay/zkay_ast/build_ast.py): Take homomorphism into account when parsing `AnnotatedTypeName`; turn calls to `addhom` / `unhom` into `RehomExpr`.  Don't make changes to add new homomorphisms here, add them to `Homomorphism` in [zkay/zkay_ast/homomorphism.py](zkay/zkay_ast/homomorphism.py) instead.

## Analysis and Type Checks

Type checking was extended to support types with different homomorphisms (non-homomorphic vs additive). The `addhom` and `unhom` keywords can only be used to change the homomorphism of an expression, and the `reveal` keyword can only be used to change the owner of an expression without changing its homomorphism. Further, homomorphic "overloads" were added to several operators. While regular operators can only operate on accessible types (`T@me` or `T@all` for some base type `T`), homomorphic operators can operate on private homomorphic values (`T@A<+>` for any `A`). To avoid developers having to litter their code with calls to `addhom` and `unhom`, basic homomorphic type inference was implemented.

**Relevant code**:
- [zkay/zkay_ast/ast.py](zkay/zkay_ast/ast.py): Contains the changes to type names in `AnnotatedTypeName`, as well as the changed `ReclassifyExpr` and its new subclass, `RehomExpr`. See also `select_homomorphic_overload` for operator overload selection.
- [zkay/type_check/type_checker.py](zkay/type_check/type_checker.py): Main changes to type checking for homomorphic types. See `visitReclassifyExpr` for `addhom` and `unhom`. See `handle_builtin_function_call` for type checking of homomorphic operators. For homomorphic type inference, see `get_rhs` and `try_rehom`.
- [zkay/zkay_ast/analysis/used_homomorphisms.py](zkay/zkay_ast/analysis/used_homomorphisms.py): Visitor that returns a list of the homomorphisms of all private values in a given AST element. This visitor is used to only include the keys of crypto backends that are used in a function, and to only include the PKI contracts of all used crypto backends in the entire contract.

## AST Transformation and Abstract Circuit Generation

The AST transformation system was adjusted such that the different ciphers, keys, etc. keep track of which crypto scheme they belong to. For each of these schemes, the correct keys need to be passed into the transformed contracts and the abstract circuit. The public keys of each crypto scheme are stored in a separate PKI contract. Homomorphic operations are implemented analogously to operations on public values that get inlined into the proof circuit.

**Relevant code**:
- [zkay/compiler/privacy/circuit_generation/circuit_helper.py](zkay/compiler/privacy/circuit_generation/circuit_helper.py):  Contains the main AST transformation changes.
- [zkay/compiler/privacy/circuit_generation/backends/jsnark_generator.py](zkay/compiler/privacy/circuit_generation/backends/jsnark_generator.py): Contains changes specific to the abstract circuit generation. Emits `o_rerand` for re-randomization of private scalar multiplications.
- [zkay/compiler/privacy/library_contracts.py](zkay/compiler/privacy/library_contracts.py): Updated public-key infrastructure (PKI) contract template.
- [zkay/compiler/privacy/transformation/zkay_contract_transformer.py](zkay/compiler/privacy/transformation/zkay_contract_transformer.py): Improved key management and PKI library imports based on homomorphisms used in function and contract.
- [zkay/compiler/privacy/transformation/zkay_transformer.py](zkay/compiler/privacy/transformation/zkay_transformer.py): Added somewhat ugly hack to support private homomorphic scalar multiplication.

## Transaction Interface Generation

The relevant API methods in `ApiWrapper` were extended with a parameter to specify which encryption scheme to use.

**Relevant code**:
- [zkay/transaction/offchain.py](zkay/transaction/offchain.py): Updated API with support for multiple crypto back-ends. Contains a new `do_homomorphic_op` method to perform homomorphic operations on suitable ciphertexts. Further,  includes a `do_rerand` function for re-randomization of ciphertext after private scalar multiplication.
- [zkay/transaction/crypto/paillier.py](zkay/transaction/crypto/paillier.py): Contains the implementation of the additively homomorphic Paillier encryption scheme, including the code perform homomorphic operations.
- [zkay/transaction/crypto/babyjubjub.py](zkay/transaction/crypto/babyjubjub.py): Implementation of elliptic curve operations on Baby Jubjub (required for ElGamal encryption).
- [zkay/transaction/crypto/elgamal.py](zkay/transaction/crypto/elgamal.py): Implementation of the additively homomorphic exponential ElGamal encryption scheme over Baby Jubjub.
- [zkay/transaction/crypto/params.py](zkay/transaction/crypto/params.py): New `CryptoParams` class used throughout the code to encapsulate the values in [meta.py](zkay/transaction/crypto/meta.py) instead of going through a global, shared `cfg` object.
- [babygiant-lib](babygiant-lib): A rust extension to efficiently compute small discrete logarithms (required for ElGamal decryption).

## Concrete Circuit Generation / Proving Back-End

The code to turn an abstract circuit into a concrete circuit can be found in the [zkay-jsnark repository](https://github.com/eth-sri/zkay-jsnark). `ZkayCircuitBase` was modified to support multiple encryption schemes, which are now encapsulated in the `CryptoBackend` class and its subclasses. For additively homomorphic encryption, Paillier, ElGamal, as well as an insecure homomorphic dummy encryption scheme were implemented. Because ElGamal encryption does not allow extracting the randomness used to form a ciphertext, we cannot re-use the encryption gadget for decryption but need a separate decryption gadget.

**Relevant code**:
- **ZkayPaillierEncGadget** and **ZkayPaillierFastEncGadget**:  Contain the implementation to perform a Paillier encryption enc(x, r) := g^x * r^n mod n^2 for a public key (n, g) in the arithmetic circuit. The "Fast" variant uses a hardcoded generator g = n + 1, which lets us save one modular exponentiation.
- **ZkayBabyJubJubGadget**: Gadget for operations on the embedded Baby Jubjub elliptic curve.
- **ZkayElgamalAddGadget**, **ZkayElgamalDecGadget**, **ZkayElgamalEncGadget**, **ZkayElgamalMulGadget** and **ZkayElgamalRerandGadget**: Gadgets to perform exponential ElGamal homomorphic addition, multiplication, encryption, decryption and rerandomization.
- **PaillierBackend**: The `CryptoBackend` for the Paillier encryption scheme. Contains the code to perform homomorphic operations on Paillier ciphertexts.
- **ElgamalBackend**: The `CryptoBackend` for the exponential ElGamal encryption scheme.
- **ZkayDummyHomEncryptionGadget**: Implementation of a homomorphic dummy encryption scheme, which "encrypts" values as enc(x, r) := x * p + 1 mod FIELD_PRIME for some prime "key" p. 1 is added to the ciphertext to prevent the encryption of 0 from creating an invalid ciphertext of 0.
- **DummyHomBackend**: The `CryptoBackend` for the homomorphic dummy encryption scheme. Again, contains the code to perform homomorphic operations on these ciphertexts.
