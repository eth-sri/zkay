import sys

from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name="babygiant-lib",
    version="1.0",
    author='Samuel Steffen, SRI Lab ETH Zurich',
    rust_extensions=[RustExtension("babygiant.babygiant", binding=Binding.RustCPython)],
    packages=["babygiant"],
    # rust extensions are not zip safe
    zip_safe=False
)
