from setuptools import setup, find_packages
test_package = 'zkay.tests'

setup(
    name='zkay',
    version='0.2',
    packages=find_packages(exclude=[f'{test_package}.compiler.output.*', f'{test_package}.transaction.output.*']),
    package_data={
        'zkay.examples': ['**/*.sol', 'scenarios/*.py'],
        'zkay.jsnark_interface': ['JsnarkCircuitBuilder.jar', 'run_snark'],
    },
    url='',
    license='',
    install_requires=[
        'Cython==0.29.14',
        'web3[tester]==v5.4.0',
        'antlr4-python3-runtime==4.7.2',
        'parameterized==0.7.1',
        'py-solc-x==0.7.0',
        'pycryptodome==3.9.4',
    ],
    python_requires='>=3.7,<4',
    author='nicbauma',
    author_email='',
    description=''
)
