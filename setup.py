import os

from setuptools import setup, find_packages
from setuptools.command.sdist import sdist
from setuptools.command.install import install
from setuptools.command.develop import develop
test_package = 'zkay.tests'
antlr_version = '4.7.2'
packages = find_packages(exclude=[f'{test_package}.compiler.output.*', f'{test_package}.transaction.output.*'])


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
        subprocess.check_call(['./build.sh', str(multiprocessing.cpu_count())], cwd=os.path.join(d, 'snark'))
        shutil.copyfile(os.path.join(d, 'snark', 'build', 'libsnark', 'zkay_interface', 'run_snark'), os.path.join(target_dir, 'run_snark'))
        perms = os.stat(os.path.join(target_dir, 'run_snark'))
        os.chmod(os.path.join(target_dir, 'run_snark'), perms.st_mode | (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


class CustomSdist(sdist):
    def run(self):
        build_grammar()
        sdist.run(self)


class CustomInstall(install):
    def run(self):
        install.run(self)
        interface_dir = os.path.join(self.install_lib, self.distribution.metadata.name, 'jsnark_interface')
        build_libsnark_backend(interface_dir)


class CustomDevelop(develop):
    def run(self):
        interface_source_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'zkay', 'jsnark_interface')
        build_grammar()
        build_libsnark_backend(interface_source_dir)
        develop.run(self)


setup(
    # Metadata
    name='zkay',
    version='0.2',
    author='nicbauma',
    author_email='nicbauma@users.noreply.gitlab.inf.ethz.ch',
    url='https://github.com/eth-sri/zkay',
    license='MIT',
    description='Specification and enforcement of data privacy in smart contracts made easy.\n'
                'The zkay package includes a compiler for the zkay language and the zkay '
                'runtime library required for issuing zkay transactions on the Ethereum blockchain.',

    # Dependencies
    python_requires='>=3.7,<4',
    install_requires=[
        'Cython==0.29.15',
        'web3[tester]==v5.5.1',
        'antlr4-python3-runtime==4.7.2',
        'parameterized==0.7.1',
        'py-solc-x==0.7.2',
        'pycryptodome==3.9.6',
        'appdirs==1.4.3',
        'argcomplete>=1,<2',
        'semantic-version>=2.8.4,<2.9',

        'pysha3>=1.0.2,<1.1', # Console script doesn't work without this even though it is not required
    ],

    # Contents
    packages=packages,
    package_data={
        'zkay.compiler.privacy': ['bn256g2.sol'],
        'zkay.examples': ['**/*.sol', 'scenarios/*.py'],
        'zkay.jsnark_interface': ['JsnarkCircuitBuilder.jar', 'bcprov-jdk15on-1.64.jar', 'run_snark'],
    },
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
