# babygiant-lib

This is a rust extension used to efficiently compute discrete logarithms for small exponents using the baby-step giant-step algorithm.

## Install

Requires rust compiler (install using `rustup` first).

_Note:_ Using the `-e` flag compiles the library in debug mode, which makes it significantly slower.

```bash
pip install .
```

## Tests

```bash
python -m unittest discover tests
```

## Uninstall

```bash
pip uninstall babygiant-lib
```
