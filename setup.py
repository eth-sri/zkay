from setuptools import setup, find_packages
test_package = 'zkay.tests'
packages = find_packages(exclude=[f'{test_package}.compiler.output.*', f'{test_package}.transaction.output.*'])

setup(
    name='zkay',
    version='0.2',
    packages=packages,
    package_data={
        'zkay.examples': ['**/*.sol', 'scenarios/*.py'],
        'zkay.jsnark_interface': ['JsnarkCircuitBuilder.jar', 'run_snark'],
    },
    url='',
    license='',
    install_requires=[
        'Cython==0.29.15',
        'web3[tester]==v5.5.1',
        'antlr4-python3-runtime==4.7.2',
        'parameterized==0.7.1',
        'py-solc-x==0.7.2',
        'pycryptodome==3.9.6',
        'appdirs==1.4.3',
    ],
    python_requires='>=3.7,<4',
    author='nicbauma',
    author_email='',
    description=''
)
