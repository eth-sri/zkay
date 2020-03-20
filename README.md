# zkay: A Blockchain Privacy Language

zkay (pronounced as `[zi: keɪ]`) is a programming language which enables
automatic compilation of intuitive data privacy specifications to NIZK-enabled
private smart contracts.

## Warning

This is an initial implementation for research purposes. There could be vulnerabilities or bugs, thus it should not be used in production yet.

## Dependencies

First, install the following dependencies with your system's package manager (python >= 3.7 is also required):

#### Debian/Ubuntu
```bash
sudo apt-get install default-jdk-headless git build-essential cmake libgmp-dev pkg-config libssl-dev libboost-dev libboost-program-options-dev
```

#### Arch Linux
```bash
sudo pacman -S --needed jdk-openjdk cmake pkgconf openssl gmp boost
```

## End-user Installation
If you simply want to use zkay as a tool, you can install it like this.
```bash
git clone <zkay-repository>
cd zkay
python3 setup.py sdist
pip3 install dist/zkay-{version}.tar.gz

# Note: Once zkay is published this simplifies to `pip3 install zkay`
```

## Development Setup
```bash
git clone <zkay-repository>
cd zkay
pip3 install -e .
```

### Using Docker

Alternatively you can also use docker to install and run zkay.
First install docker, then you can run the image as follows:

```bash
/path/to/zkay$ ./zkay-docker.sh
(base) root@ae09e165bd19:/zkay_host$
```

This command mounts the directory `zkay` from your host as `/zkay_host`
within the docker container. You can run `zkay-docker.sh` also from any other directory `d` on your host.
In this case, `d` is mounted as `/d_host` inside the container.
This allows you to operate on files from your host machine.


### Unit Tests

To run all unit tests, use:
```bash
python3 -m unittest discover --verbose zkay
```

## Usage

### Type-Check Contracts

To type-check a zkay file `test.zkay` without compiling it, run:

```bash
zkay check test.zkay
```

### Strip zkay features from contract

To output a source-location-preserving public solidity
contract which corresponds to `test.zkay` but with all privacy features removed (useful for running analysis tools designed for solidity), run:

```bash
zkay solify test.zkay
```

The transformed code is printed to stdout.

### Deploy library contracts
zkay requires a crypto-backend dependent external PKI (public key infrastructure) contract and
depending on the proving-scheme also additional library contracts on the blockchain to function.

These contracts can be compiled and deployed using the commands:

```bash
zkay deploy-pki --node-uri <local eth node uri> --account <address>
zkay deploy-crypto-libs --node-uri <local eth node uri> --account <address>
```

[//]: # (We should probably deploy official pki and library contracts on testnet [maybe mainnet],
         to which zkay can connect by default)

### Compile Contracts

To compile a zkay file `test.zkay`

```bash
zkay compile [-o "<output_dir>"] test.zkay
```

This performs the following steps
- Type checking
- Transformation from zkay -> solidity
- NIZK proof circuit compilation and key generation
- Generation of `contract.py` (interface code which does automatic transaction transformation to interact with the zkay contract)

### Package Contract For Distribution

To package a zkay contract which was previously compiled with output directory "./zkay_out" for distribution, run:

```bash
zkay export [-o "<output_filename>"] ./zkay_out
```

This will create an archive, which contains the zkay code, a manifest and the snark keys.
The recommended file extension is `*.zkp`.

### Unpack Packaged Contract

To unpack and compile a contract package `contract.zkp`, which was previously created using `zkay export`:

```bash
zkay import [-o "<unpack_directory>"] contract.zkp
```


### Interact with contract

Assuming you have previously compiled a file `test.zkay` with `zkay compile -o "output_dir"` or
have imported a file `contract.zkp` using `zkay import -o "output_dir" contract.zkp`

```bash
zkay run output_dir

# Or alternatively
# cd output_dir
# python3 contract.py
>>> ...
```

You are now in a python shell where you can issue the following commands:
- `help()`: Get a list of all contract functions with arguments
- `user1, user2, ..., userN = create_dummy_accounts(N)`: Get addresses of pre-funded test accounts for experimentation (only supported in w3-eth-tester and w3-ganache backend)
- `handle = deploy(*constructor_args, user: str)`: Issue a deployment transaction for the contract from the account `user` (address literal).
- `handle = connect(contract_addr: str, user: str)`: Create a handle to interact with the deployed contract at address `contract_addr` from account `user`
- `handle.address`: Get the address of the deployed contract corresponding to this handle
- `handle.some_func(*args[, value: int])`: The account which created handle issues a zkay transaction which calls the zkay contract function `some_func` with the given arguments.
Encryption, transaction transformation and proof generation happen automatically. If the function is payable, the additional argument `value` can be used to set the wei amount to be transferred.
- `handle.api.req_state_var(name: str, *indices, count=0, should_decrypt: bool=False)`: Retrieve the current value of state variable `name[indices[0]][indices[1]][...]`.
If the state variable is owned by you, you can specify should_decrypt=True to get the decrypted value.

There are also two more specific commands for deploying or connecting to a single contract instance.
The contract instance functions are then available as global functions in the shell.

#### Deploy a zkay contract

```bash
zkay deploy output_dir <constructor_args...>
```

#### Connect to and interact with contract instance

```bash
zkay connect output_dir contract_address
```
