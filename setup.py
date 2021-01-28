import os

from setuptools import setup, find_packages
from setuptools.command.sdist import sdist
from setuptools.command.install import install
from setuptools.command.develop import develop


def _read_file(path: str) -> str:
    with open(path) as f:
        return f.read().strip()


# Versions
antlr_version = '4.8'
file_dir = os.path.dirname(os.path.realpath(__file__))
zkay_version = _read_file(os.path.join(file_dir, 'zkay', 'VERSION'))
zkay_libsnark_commit_hash = 'ec640cd4e4bb061f89d6f070ebff1c1c7536a24e'
packages = find_packages()


def build_grammar():
    source_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'zkay')
    antlr_jar_name = f'antlr-{antlr_version}.jar'
    antlr_jar_path = os.path.join(source_dir, 'solidity_parser', antlr_jar_name)
    if not os.path.exists(antlr_jar_path):
        # Download antlr if necessary
        import urllib.request
        urllib.request.urlretrieve(f'https://www.antlr.org/download/antlr-{antlr_version}-complete.jar', antlr_jar_path)
    import subprocess
    subprocess.check_call(['java', '-jar', antlr_jar_name, '-o', 'generated', '-visitor', '-Dlanguage=Python3', 'Solidity.g4'],
                          cwd=os.path.dirname(os.path.realpath(antlr_jar_path)))


def build_libsnark_backend(target_dir: str):
    import subprocess
    import multiprocessing
    import shutil
    import stat
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        subprocess.check_call(['git', 'clone', '--recursive', 'https://github.com/eth-sri/zkay-libsnark.git', 'snark'], cwd=d)
        subprocess.check_call(['git', 'checkout', zkay_libsnark_commit_hash], cwd=os.path.join(d, 'snark'))
        subprocess.check_call(['./build.sh', str(multiprocessing.cpu_count())], cwd=os.path.join(d, 'snark'))
        shutil.copyfile(os.path.join(d, 'snark', 'build', 'libsnark', 'zkay_interface', 'run_snark'), os.path.join(target_dir, 'run_snark'))
        perms = os.stat(os.path.join(target_dir, 'run_snark'))
        os.chmod(os.path.join(target_dir, 'run_snark'), perms.st_mode | (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def install_latest_compatible_solc():
    import solcx
    from zkay.config_version import Versions
    solcx.install_solc_pragma(Versions.ZKAY_SOLC_VERSION_COMPATIBILITY.expression)


class CustomSdist(sdist):
    def run(self):
        build_grammar()
        sdist.run(self)


class CustomInstall(install):
    def run(self):
        install.run(self)
        interface_dir = os.path.join(self.install_lib, self.distribution.metadata.name, 'jsnark_interface')
        build_libsnark_backend(interface_dir)
        install_latest_compatible_solc()


class CustomDevelop(develop):
    def run(self):
        interface_source_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'zkay', 'jsnark_interface')
        build_grammar()
        build_libsnark_backend(interface_source_dir)
        develop.run(self)
        install_latest_compatible_solc()


setup(
    # Metadata
    name='zkay',
    version=zkay_version,
    author='Nick Baumann, SRI Lab ETH Zurich',
    url='https://github.com/eth-sri/zkay',
    license='MIT',
    description='Zkay is a programming language which enables automatic compilation of intuitive data privacy specifications to Ethereum smart contracts leveraging encryption and non-interactive zero-knowledge (NIZK) proofs. The zkay package provides a toolchain for compiling, deploying and using zkay contracts.',

    # Dependencies
    python_requires='>=3.8,<4',
    install_requires=[
        'Cython>=0.29,<0.30',
        'web3[tester]>=v5.11,<v5.13',
        f'antlr4-python3-runtime=={antlr_version}',
        'parameterized>=0.7,<0.8',
        'py-solc-x>=1.0.0,<1.1.0',
        'pycryptodome>=3.9,<4',
        'appdirs>=1.4,<1.5',
        'argcomplete>=1,<2',
        'semantic-version>=2.8.4,<2.9',

        'pysha3>=1.0.2,<1.1', # Console script doesn't work without this even though it is not required
    ],

    # Contents
    packages=packages,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "zkay=zkay.__main__:main"
        ]
    },

    # Build steps
    cmdclass={
        'sdist': CustomSdist,
        'install': CustomInstall,
        'develop': CustomDevelop
    }
)
