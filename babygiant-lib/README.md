# babygiant-lib

This is a rust extension to efficiently compute discrete logarithms for small exponents using the baby-step giant-step algorithm.

## Install

### From wheel (recommended)

Install using precompiled binary (select `whl` file matching your platform; use `pip debug --verbose` to show compatible tags):

```bash
pip install dist/babygiant_lib-1.0-<your-architecture>.whl
```

### From source

Installing from source requires the rust compiler toolchain (install using `rustup` first).

```bash
pip install .
```

## Tests

```bash
cd tests
python -m unittest discover .
```

## Build Wheels

According to [here](https://github.com/PyO3/setuptools-rust):

```bash
docker pull quay.io/pypa/manylinux2014_x86_64
docker run --rm -v `pwd`:/io quay.io/pypa/manylinux2014_x86_64 bash /io/build-wheels.sh
```

## Uninstall

```bash
pip uninstall babygiant-lib
```
