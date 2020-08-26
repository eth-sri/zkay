# zkay: A Blockchain Privacy Language

Zkay (pronounced as `[zi: keɪ]`) is a programming language which enables automatic compilation of intuitive data privacy specifications to Ethereum smart contracts leveraging encryption and zero-knowledge (NIZK) proofs. This repository provides a toolchain for compiling, deploying and using zkay contracts.

In addition to the instructions below, we refer to the following resources:

- The original [research paper][zkay-ccs], which introduces the core concepts of zkay.
- The [online documentation][zkay-docs], which provides a tutorial, language reference and API documentation.
- The [technical report][zkay-0.2-techreport], which describes the features and implementation of zkay v0.2.

## Warning / Security Disclaimer

Zkay is a research project and its implementation is **not secure**! Do not use zkay in a
productive system or to process confidential data.

## Prerequisites

Zkay requires python version 3.7 or later to be installed. Additionally, install the following dependencies using your system's package manager:

#### Debian/Ubuntu
```bash
sudo apt-get install default-jdk-headless git build-essential cmake libgmp-dev pkg-config libssl-dev libboost-dev libboost-program-options-dev
```

#### Arch Linux
```bash
sudo pacman -S --needed jdk-openjdk cmake pkgconf openssl gmp boost
```

## Installation for Users
If you only want to use zkay as a tool, you can install it as follows.

```bash
git clone git@github.com:eth-sri/zkay.git
cd zkay
python3 setup.py sdist
pip3 install --no-binary zkay ./dist/zkay-*.tar.gz

# Note: Once zkay is published, this simplifies to `pip3 install --no-binary zkay zkay`
```

## Installation for Developers
For development of zkay, install zkay in editable mode as follows.

```bash
git clone git@github.com:eth-sri/zkay.git
cd zkay
pip3 install -e .
```

### Using Docker

Alternatively, you can also set up zkay in a docker container using the provided Dockerfile in the `install` subdirectory.

To build and run the image, you can simply use:

```bash
cd install
make -C ./install run
```

### Unit Tests

To run all unit tests, use:
```bash
cd zkay
python3 -m unittest discover --verbose zkay
```

### Building the Docs

The documentation is hosted [here][zkay-docs]. To build it locally, use the following commands (requires sphinx, sphinx-rtd-theme, and sphinx-autoapi):

```bash
cd docs
make html
```

The above commands create a tree of HTML files in `_build/html`. Developers with sufficient access rights can publish the documentation on GitHub Pages using the script `publish_gh_pages.sh`.


## Usage

See the [online documentation][zkay-docs] for a tutorial on how to use zkay. Below, we only show a summary of available commands.

**Note**: zkay supports tab completion in Bash shells via the argcomplete package.
To enable this feature, argcomplete must be installed and activated on your system (see [instructions](https://kislyuk.github.io/argcomplete/#installation)).

### Type-check Contracts

To type-check a zkay file `test.zkay` without compiling it, run:

```bash
zkay check test.zkay
```

### Strip zkay Features from Contract

To strip zkay-specific features from `test.zkay` and output the resulting (location preserving) Solidity code, run:

```bash
zkay solify test.zkay
```

The transformed code is printed to stdout.

### Deploy Library Contracts

Zkay requires a backend-dependent external public key infrastructure (PKI) contract and, depending on the proving scheme, additional library contracts to be deployed. These contracts can be compiled and deployed using the commands:

```bash
zkay deploy-pki <account>
zkay deploy-crypto-libs <account>
```
The `account` parameter specifies the wallet address from which the deployment transaction should be issued.

**Note**: The `groth16` proving scheme (enabled by default) does not require additional libraries, in which case `zkay deploy-crypto-libs` is not required.

**Note**: The default `eth-tester` blockchain backend does not require manually deploying the PKI or library contracts.

### Compile Contracts

To compile a zkay file `test.zkay`, run:

```bash
zkay compile [-o "<output_dir>"] test.zkay
```

This performs the following steps:
- Type checking (equivalent to `zkay check`)
- Compilation to Solidity
- NIZK proof circuit compilation and key generation
- Generation of the contract interface `contract.py`, which can be used to transparently interact with a deployed zkay contract

### Exporting a Contract Package

To package a zkay contract that was previously compiled with output directory `<compilation_output>`, run:

```bash
zkay export [-o "<output_filename>"] "<compilation_output>"
```

This creates an archive containing the zkay code, the NIZK prover and verifier keys, and manifest file. The recommended file extension for the archive is `*.zkp`. This archive can be distributed to users of the contract.

### Importing a Contract Package

To unpack and compile a contract package `contract.zkp`:

```bash
zkay import [-o "<unpack_directory>"] contract.zkp
```

### Interacting with a Contract

Assume you have compiled a file `test.zkay` using `zkay compile -o "output_dir"` (or imported an archive `contract.zkp` using `zkay import -o "output_dir" contract.zkp`), you can open an interactive shell for deploying and interacting with the contract as follows:

```bash
zkay run output_dir
>>> ...
```

The python shell provides the following commands:
- `help()`: Get a list of all contract functions and their arguments
- `user1, user2, ..., userN = create_dummy_accounts(N)`: Get addresses of pre-funded test accounts for experimentation (only supported in `eth-tester` and `ganache` backends)
- `handle = deploy(*constructor_args, user: str)`: Issue a deployment transaction for the contract from the account `user` (address literal).
- `handle = connect(contract_addr: str, user: str)`: Create a handle to interact with the deployed contract at address `contract_addr` from account `user`.
Fails if remote contract does not match local files.
- `handle.address`: Get the address of the deployed contract corresponding to this handle
- `handle.some_func(*args[, value: int])`: The account which created handle issues a zkay transaction which calls the zkay contract function `some_func` with the given arguments.
Encryption, transaction transformation and proof generation happen automatically. If the function is payable, the additional argument `wei_amount` can be used to set the wei amount to be transferred.
- `handle.state.get_raw('varname', *indices)`: Retrieve the current raw value of state variable `name[indices[0]][indices[1]][...]`.
- `handle.state.get_plain('varname', *indices)`: Retrieve the current plaintext value (decrypted with @me key if necessary) of state variable `name[indices[0]][indices[1]][...]`.


### Update Solc to Latest Compatible Version

To download and install the latest compatible version of solc (requires internet connection):

```bash
zkay update-solc
```

## Citing this Work

You are encouraged to cite the following [research paper][zkay-ccs] if you use zkay for academic research.
```
@inproceedings{steffen2019zkay,
    author = {Steffen, Samuel and Bichsel, Benjamin and Gersbach, Mario and Melchior, Noa and Tsankov, Petar and Vechev, Martin},
    title = {Zkay: Specifying and Enforcing Data Privacy in Smart Contracts},
    year = {2019},
    isbn = {9781450367479},
    publisher = {Association for Computing Machinery},
    address = {New York, NY, USA},
    url = {https://doi.org/10.1145/3319535.3363222},
    doi = {10.1145/3319535.3363222},
    booktitle = {Proceedings of the 2019 ACM SIGSAC Conference on Computer and Communications Security},
    pages = {1759–1776},
    numpages = {18},
    location = {London, United Kingdom},
    series = {CCS ’19}
}
```

The following [technical report][zkay-0.2-techreport] describes version 0.2 of zkay, which introduces many vital features such as real encryption.
```
TODO BibTex
```


[zkay-ccs]: https://www.sri.inf.ethz.ch/publications/steffen2019zkay
[zkay-docs]: https://eth-sri.github.io/zkay
[zkay-0.2-techreport]: TODO
