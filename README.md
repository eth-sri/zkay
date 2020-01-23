# zkay: A Blockchain Privacy Language

zkay (pronounced as `[zi: keɪ]`) is a programming language which enables
automatic compilation of intuitive data privacy specifications to NIZK-enabled
private smart contracts.

## Warning

This is a prototype implementation not intended for use in production. In
particular, it uses "dummy" encryption `Enc(v,R,k)=v+k` by default, which is **insecure**.

## Install

First make sure to install the Java Development Kit: `openjdk-{>=8}-jdk (on debian derivatives)` and `python >= 3.7`.

Then set up other prerequisites using:
```bash
./build_deps.sh
```

### Using PIP

To build the python package:

```bash
python3 setup.py sdist
```

Variant 1: Install zkay in default package location
```bash
pip3 install dist/zkay-{VERSION}.tar.gz
```

Variant 2: Install zkay in new virtual environment

```bash
# Create new venv
python3 -m venv zkay-venv

# Source venv
source zkay-venv/bin/activate

# Install zkay
(zkay-venv) pip3 install dist/zkay-{VERSION}.tar.gz
```

From now on this readme assumes that your shell is in the python environment in which you installed zkay.
So if you used variant 2, you have to activate the venv (once per shell) before issuing any other zkay commands or using
`contract.py` (contract interface generated during compilation):
```bash
source zkay-venv/bin/activate
(zkay-venv)  ...
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

## Unit Tests

To run all unit tests of zkay, run:
```bash
(zkay-venv) python3 -m unittest discover --verbose zkay
```

## Type-Check Contracts

To type-check a zkay file `test.zkay` without compiling it, run:

```bash
(zkay-venv) python3 -m zkay --type-check test.zkay
```

## Fake solidity transformation

To output a source-location-preserving public solidity
contract which corresponds to `test.zkay` but with all privacy features removed, run:

```bash
(zkay-venv) python3 -m zkay --output-fake-solidity --output "<output_dir>" test.zkay
```

## Compile Contracts

To compile a zkay file `test.zkay`

```bash
(zkay-venv) python3 -m zkay --output "<output_dir>" test.zkay
```

This performs the following steps
- Type checking
- Transformation from zkay -> solidity
- NIZK proof circuit compilation and key generation
- Generation of `contract.py` (interface code which does automatic transaction transformation to interact with the zkay contract)

## Interact with contract

Assuming you have previously compiled a file `test.zkay` with --output "output_dir"

```bash
(zkay-venv) cd output_dir
(zkay-venv) python contract.py
>>> ...
```

You are now in a python shell where you can issue the following commands:
- `help()`: Get a list of all contract functions with arguments
- `user1, user2, ..., userN = create_dummy_accounts(N)`: Get addresses of pre-funded test accounts for experimentation (only supported in eth-tester backend)
- `handle = deploy(*constructor_args, user: str)`: Issue a deployment transaction for the contract from the account `user` (address literal).
- `handle = connect(contract_addr: str, user: str)`: Create a handle to interact with the deployed contract at address `contract_addr` from account `user`
- `handle.address`: Get the address of the deployed contract corresponding to this handle
- `handle.some_func(*args[, value: int])`: The account which created handle issues a zkay transaction which calls the zkay contract function `some_func` with the given arguments.
Encryption, transaction transformation and proof generation happen automatically. If the function is payable, the additional argument `value` can be used to set the wei amount to be transferred.
- `handle.get_state(name: str, *indices, is_encrypted: bool=False)`: Retrieve the current value of state variable `name[indices[0]][indices[1]][...]`.
If the state variable is not owned by @all, you can specify is_encrypted=True to get the decrypted value.
