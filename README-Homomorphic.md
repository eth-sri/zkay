# Homomorphic Encryption in zkay

This file is intended to give new or returning contributors an overview of where in the project the various homomorphic features are implemented.
Changes are grouped by subsystem, see Fig. 2 (p. 12) of the [zkay 0.2 tech report](https://arxiv.org/pdf/2009.01020.pdf).

## Parsing

In "non-homomorphic" zkay, types have the form `T@A` (e.g. `uint@owner`) where `T` is some basic Solidity type and `A` is the privacy label.
We split up the type system into non-homomorphic types `T@A<>` and additively homomorphic types `T@A<+>`.
Other homomorphic types are possible, but only non-homomorphic and additively homomorphic types have been implemented so far.
Just like `uint` is an alias for `uint@all` in regular zkay, `uint@owner` is an alias for `uint@owner<>` in homomorphic zkay.

Further, we add two new keywords, `addhom` and `unhom`, to convert between non-homomorphic and homomorphic types.

**Relevant code**:
- [solidity_parser/Solidity.g4](zkay/solidity_parser/Solidity.g4):
  Syntax for homomorphic type names. See `homomorphismAnnotation` for `<>` / `<+>` tags.
  After making changes, make sure that antlr 4.8 or newer is installed, then run [solidity_parser/Makefile](zkay/solidity_parser/Makefile).
- [compiler/solidity/fake_solidity_generator.py](zkay/compiler/solidity/fake_solidity_generator.py):
  Extended the RegEx that turns private zkay code into fake public Solidity code to also remove `addhom` / `unhom` (we piggy-back on the Solidity compiler for basic type checking).
- [zkay_ast/build_ast.py](zkay/zkay_ast/build_ast.py): Take homomorphism into account when parsing `AnnotatedTypeName`; turn calls to `addhom` / `unhom` into `RehomExpr`.
  Don't make changes to add new homomorphisms here, add them to `Homomorphism` in [zkay_ast/homomorphism.py](zkay/zkay_ast/homomorphism.py) instead.

## Analysis and Type Checks

Type checking was extended to support types with different homomorphisms (non-homomorphic vs additive).
The `addhom` and `unhom` keywords can only be used to change the homomorphism of a value, and the `reveal` keyword can only be used to change the privacy of a value without changing its homomorphism.
Further, homomorphic "overloads" have been added to several operators.
While regular operators can only operate on accessible types (`T@me` or `T@all` for some base type `T`), homomorphic operators can operate on arbitrary private homomorphic values (`T@A<+>` for any `A`).
Operator "overload" selection works as follows: if at least one argument is inaccessible, select the homomorphic operator overload. If all arguments are accessible, select the non-homomorphic overload.
Finally, to avoid developers having to litter their code with calls to `addhom` and `unhom`, basic homomorphic type inference was implemented.

**Relevant code**:
- [zkay_ast/ast.py](zkay/zkay_ast/ast.py):
  Contains the changes to type names in `AnnotatedTypeName`, as well as the changed `ReclassifyExpr` and its new subclass, `RehomExpr`.
  See also `select_homomorphic_overload` for operator overload selection.
- [type_check/type_checker.py](zkay/type_check/type_checker.py):
  Main changes to type checking for homomorphic types.
  See `visitReclassifyExpr` for `addhom` and `unhom`.
  See `handle_builtin_function_call` for type checking of homomorphic operators.
  For homomorphic type inference, see `get_rhs` and `try_rehom`.
- [zkay_ast/analysis/used_homomorphisms.py](zkay/zkay_ast/analysis/used_homomorphisms.py):
  Visitor that returns a list of the homomorphisms of all private values in a given AST element.
  This visitor is used to only include the keys of crypto backends that are used in a function,
  and to only include the PKI contracts of all used crypto backends in the entire contract.

## AST Transformation and Abstract Circuit Generation

As the type system now supports different homomorphisms, we need to make use of different encryption schemes which support these homomorphisms.
The AST transformation system was thus adjusted such that the different ciphers, keys, etc. keep track of which crypto scheme they belong to.
For each of these schemes, the correct keys need to be passed into the transformed contracts and the abstract circuit.
The public keys of each crypto scheme are stored in a separate PKI contract.
This should help prevent keys being mixed up between different crypto schemes and will make future key verification easier.

Homomorphic operations are implemented like operations on public values that get inlined into the proof circuit (which makes sense as the *ciphertexts* are public).
That is, currently we compute the correct result of a homomorphic operation off-chain and prove its correctness using a zk-SNARK proof instead of performing the homomorphic operation on-chain.
The rationale behind this is that proving the correctness of homomorphic operations (unlike proving the correctness of homomorphic encryption constraints) is cheap in zk-SNARK circuits,
whereas performing modular arithmetic on arbitrary-length integers on Ethereum is rather expensive in terms of gas costs.

**Relevant code**:
- [compiler/privacy/circuit_generation/circuit_helper.py](zkay/compiler/privacy/circuit_generation/circuit_helper.py):
  Contains the main AST transformation changes.
- [compiler/privacy/circuit_generation/backends/jsnark_generator.py](zkay/compiler/privacy/circuit_generation/backends/jsnark_generator.py):
  Contains changes specific to the abstract circuit generation.
- [compiler/privacy/library_contracts.py](zkay/compiler/privacy/library_contracts.py):
  Updated public-key infrastructure (PKI) contract template.
  One instantiated PKI contract is imported for each encryption scheme used in the contract.
- [compiler/privacy/transformation/zkay_contract_transformer.py](zkay/compiler/privacy/transformation/zkay_contract_transformer.py):
  Improved key management and PKI library imports based on homomorphisms used in function / contract.

## Transaction Interface Generation

The generated Python code also needs to be able to support using multiple encryption schemes in one contract,
so the relevant API methods in `ApiWrapper` were extended with a parameter to specify which scheme to use.
Moreover, to be able to create proofs for the correct execution of homomorphic operations,
we also have to be able to perform these homomorphic operations from the generated Python code.

**Relevant code**:
- [transaction/offchain.py](zkay/transaction/offchain.py):
  Updated API with support for multiple crypto back-ends.
  Also contains a new `do_homomorphic_op` method to perform homomorphic operations on suitable ciphertexts.
- [transaction/crypto/paillier.py](zkay/transaction/crypto/paillier.py):
  Contains the implementation of the additively homomorphic Paillier encryption scheme, including the code perform homomorphic operations.
  When adding other homomorphic encryption schemes, make sure to extend `ZkayHomomorphicCryptoInterface` instead of `ZkayCryptoInterface`, and implement `do_op`.
- [transaction/crypto/params.py](zkay/transaction/crypto/params.py):
  New `CryptoParams` class used throughout the code to encapsulate the values in [meta.py](zkay/transaction/crypto/meta.py)
  instead of going through a global, shared `cfg` object (which inherently prevents supporting multiple crypto-backends). 

## Concrete Circuit Generation / Proving Back-End

The code to turn an abstract circuit into a concrete circuit can be found in the zkay-jsnark repository, which contains zkay's fork of the jsnark circuit generation library.
For example, an check such as `checkEnc(...)` in the generated Java code is translated into an actual encryption performed on circuit wires.
For these generated concrete circuits, we can then generate zero-knowledge proofs using libsnark.

`ZkayCircuitBase` was modified to support multiple encryption schemes, which are now encapsulated in the `CryptoBackend` class and its subclasses.
For additively homomorphic encryption, the Paillier encryption scheme as well as an insecure homomorphic dummy encryption scheme were implemented.

**Relevant code**:
- **ZkayPaillierEncGadget** and **ZkayPaillierFastEncGadget**:
  Contain the implementation to perform a Paillier encryption enc(x, r) := g^x * r^n mod n^2 for a public key (n, g) in the arithmetic circuit.
  The **Fast** variant uses a hardcoded generator g = n + 1, which lets us save one modular exponentiation.
- **PaillierBackend**:
  The `CryptoBackend` for the Paillier encryption scheme.
  Contains the code to perform homomorphic operations on Paillier ciphertexts.
- **ZkayDummyHomEncryptionGadget**:
  Implementation of a homomorphic dummy encryption scheme, which "encrypts" values as enc(x, r) := x * p + 1 mod FIELD_PRIME for some prime "key" p.
  1 is added to the ciphertext to prevent the encryption of 0 from creating an invalid ciphertext of 0.
- **DummyHomBackend**:
  The `CryptoBackend` for the homomorphic dummy encryption scheme.
  Again, contains the code to perform homomorphic operations on these ciphertexts.

## Homomorphic contract examples

| Contract name             | Description |
| ------------------------- |-------------|
| [ExposureWarning][E1]     | A contract that uses homomorphic addition to tally the number of exposures to people infected with "some" infectious disease.
| [IndexFund][E2]           | An index fund tracking a number of stocks. Can prove that the correct number of stocks was bought using multiplication between an additively homomorphic and a public value.
| [Inheritance][E3]         | A contract allowing inheriting tokens from another user if that user set up a will and has not checked in for some time.
| [Interest][E4]            | Built on top of [TokenHomomorphic][E9], this contract allows users to add a percentage-based amount of interest to invested tokens for each unit of time that passed.
| [NGO][E5]                 | Similar to [IndexFund][E2], this contract allows NGOs to prove that the correct amount of a user's investment has been put towards the advertised causes.
| [ReceiptsHomomorphic][E6] | Extends the [Receipts](zkay/examples/code/Receipts.zkay) contract. Tallies both income and expenses using addition on homomorphic types to calculate a business's balance.
| [Referendum][E7]          | A contract to vote "yes" or "no" to a referendum without revealing one's vote to anyone. Votes are counted using homomorphic addition.
| [ReviewsHomomorphic][E8]  | Extends the [Reviews](zkay/examples/code/Reviews.zkay) contract. Using homomorphic addition, an arbitrary number of reviewers can now review any submitted paper.
| [TokenHomomorphic][E9]    | Transfer tokens between addresses. The balance of the recipient is adjusted using homomorphic subtraction.The recipient does not have to perform an Ethereum transaction to "accept" the incoming tokens.
| [VotingBooth][E10]        | Vote for one of multiple candidates revealing one's vote to just a single party. Votes are counted using homomorphic addition.

[E1]: zkay/examples/code/ExposureWarning.zkay
[E2]: zkay/examples/code/IndexFund.zkay
[E3]: zkay/examples/code/Inheritance.zkay
[E4]: zkay/examples/code/Interest.zkay
[E5]: zkay/examples/code/Ngo.zkay
[E6]: zkay/examples/code/ReceiptsHomomorphic.zkay
[E7]: zkay/examples/code/Referendum.zkay
[E8]: zkay/examples/code/ReviewsHomomorphic.zkay
[E9]: zkay/examples/code/TokenHomomorphic.zkay
[E10]: zkay/examples/code/VotingBooth.zkay
