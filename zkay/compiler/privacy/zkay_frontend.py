"""
This module exposes functionality to compile and package zkay code
"""
import importlib
import json
import os
import re
import shutil
import sys
import tempfile
from copy import deepcopy
from typing import Tuple, List, Type, Dict, Optional, Any

from zkay import my_logging
from zkay.compiler.privacy import library_contracts
from zkay.compiler.privacy.circuit_generation.backends.jsnark_generator import JsnarkGenerator
from zkay.compiler.privacy.circuit_generation.circuit_generator import CircuitGenerator
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.manifest import Manifest
from zkay.compiler.privacy.offchain_compiler import PythonOffchainVisitor
from zkay.compiler.privacy.proving_scheme.backends.gm17 import ProvingSchemeGm17
from zkay.compiler.privacy.proving_scheme.proving_scheme import ProvingScheme
from zkay.compiler.privacy.transformation.zkay_contract_transformer import transform_ast
from zkay.compiler.solidity.compiler import check_compilation
from zkay.config import cfg
from zkay.utils.helpers import read_file, lines_of_code, without_extension
from zkay.utils.progress_printer import print_step
from zkay.utils.timer import time_measure
from zkay.zkay_ast.process_ast import get_processed_ast, get_verification_contract_names

proving_scheme_classes: Dict[str, Type[ProvingScheme]] = {
    'gm17': ProvingSchemeGm17
}

generator_classes: Dict[str, Type[CircuitGenerator]] = {
    'jsnark': JsnarkGenerator
}


def compile_zkay_file(input_file_path: str, output_dir: str, import_keys: bool = False, **kwargs):
    """
    Parse, type-check and compile the given zkay contract file.

    :param input_file_path: path to the zkay contract file
    :param output_dir: path to a directory where the compilation output should be generated
    :param import_keys: | if false, zk-snark of all modified circuits will be generated during compilation
                        | if true, zk-snark keys for all circuits are expected to be already present in the output directory, and the compilation will use the provided keys to generate the verification contracts
                        | This option is mostly used internally when connecting to a zkay contract provided by a 3rd-party
    :raise ZkayCompilerError: if any compilation stage fails
    :raise RuntimeError: if import_keys is True and zkay file, manifest file or any of the key files is missing
    """
    code = read_file(input_file_path)

    # log specific features of compiled program
    my_logging.data('originalLoc', lines_of_code(code))
    m = re.search(r'\/\/ Description: (.*)', code)
    if m:
        my_logging.data('description', m.group(1))
    m = re.search(r'\/\/ Domain: (.*)', code)
    if m:
        my_logging.data('domain', m.group(1))
    _, filename = os.path.split(input_file_path)

    # compile
    with time_measure('compileFull'):
        cg, _ = compile_zkay(code, output_dir, import_keys, **kwargs)


def compile_zkay(code: str, output_dir: str, import_keys: bool = False, **kwargs) -> Tuple[CircuitGenerator, str]:
    """
    Parse, type-check and compile the given zkay code.

    Note: If a SolcException is raised, this indicates a bug in zkay
          (i.e. zkay produced solidity code which doesn't compile, without raising a ZkayCompilerError)

    :param code: zkay code to compile
    :param output_dir: path to a directory where the compilation output should be generated
    :param import_keys: | if false, zk-snark of all modified circuits will be generated during compilation
                        | if true, zk-snark keys for all circuits are expected to be already present in the output directory, \
                          and the compilation will use the provided keys to generate the verification contracts
                        | This option is mostly used internally when connecting to a zkay contract provided by a 3rd-party
    :raise ZkayCompilerError: if any compilation stage fails
    :raise RuntimeError: if import_keys is True and zkay file, manifest file or any of the key files is missing
    """

    # Copy zkay code to output
    zkay_filename = 'contract.zkay'
    if import_keys and not os.path.exists(os.path.join(output_dir, zkay_filename)):
        raise RuntimeError('Zkay file is expected to already be in the output directory when importing keys')
    elif not import_keys:
        _dump_to_output(code, output_dir, zkay_filename)

    # Type checking
    zkay_ast = get_processed_ast(code)

    # Contract transformation
    with print_step("Transforming zkay -> public contract"):
        ast, circuits = transform_ast(deepcopy(zkay_ast))

    # Dump libraries
    with print_step("Write library contract files"):
        # Write pki contract
        _dump_to_output(library_contracts.get_pki_contract(), output_dir, f'{cfg.pki_contract_name}.sol', dryrun_solc=True)

        # Write library contract
        _dump_to_output(library_contracts.get_verify_libs_code(), output_dir, ProvingScheme.verify_libs_contract_filename, dryrun_solc=True)

    # Write public contract file
    with print_step('Write public solidity code'):
        output_filename = 'contract.sol'
        solidity_code_output = _dump_to_output(ast.code(), output_dir, output_filename)

    # Get all circuit helpers for the transformed contract
    circuits: List[CircuitHelper] = list(circuits.values())

    # Generate offchain simulation code (transforms transactions, interface to deploy and access the zkay contract)
    offchain_simulation_code = PythonOffchainVisitor(circuits).visit(ast)
    _dump_to_output(offchain_simulation_code, output_dir, 'contract.py')

    # Instantiate proving scheme and circuit generator
    ps = proving_scheme_classes[cfg.proving_scheme]()
    cg = generator_classes[cfg.snark_backend](circuits, ps, output_dir)

    if 'verifier_names' in kwargs:
        assert isinstance(kwargs['verifier_names'], list)
        verifier_names = get_verification_contract_names(zkay_ast)
        assert sorted(verifier_names) == sorted([cc.verifier_contract_type.code() for cc in cg.circuits_to_prove])
        kwargs['verifier_names'][:] = verifier_names[:]

    # Generate manifest
    if not import_keys:
        with print_step("Writing manifest file"):
            manifest = {
                Manifest.zkay_version: cfg.zkay_version,
                Manifest.solc_version: cfg.solc_version,
                Manifest.zkay_options: cfg.export_compiler_settings(),
            }
            _dump_to_output(json.dumps(manifest), output_dir, 'manifest.json')
    elif not os.path.exists(os.path.join(output_dir, 'manifest.json')):
        raise RuntimeError('Zkay contract import failed: Manifest file is missing')

    # Generate circuits and corresponding verification contracts
    cg.generate_circuits(import_keys=import_keys)

    # Check that all verification contracts and the main contract compile
    main_solidity_files = cg.get_verification_contract_filenames() + [os.path.join(output_dir, output_filename)]
    for f in main_solidity_files:
        check_compilation(f, show_errors=False)

    return cg, solidity_code_output


def load_transaction_interface_from_directory(contract_dir: str) -> Any:
    """
    Load transaction interface module for contracts in contract_dir

    :param contract_dir: directory with zkay contract compilation output
    :return: module object
    """
    sys.path.append(str(os.path.realpath(contract_dir)))
    contract_mod = importlib.import_module(f'contract')
    importlib.reload(contract_mod)
    sys.path.pop()
    return contract_mod


def load_contract_transaction_interface_from_module(contract_mod: Any,
                                                    contract_name: Optional[str] = None) -> Type:
    """
    Load contract class from transaction interface module

    :param contract_mod: loaded transaction interface module
    :param contract_name: contract name, only required if file contains multiple contracts
    :return: Contract class
    """

    contracts = {}
    for name, cls in contract_mod.__dict__.items():
        if isinstance(cls, type) and 'ContractSimulator' in [b.__name__ for b in cls.__bases__]:
            contracts[cls.__name__] = cls

    if contract_name is None:
        if len(contracts) != 1:
            raise ValueError('If file contains multiple contracts, contract name must be specified')
        return next(iter(contracts.values()))
    else:
        return contracts[contract_name]


def load_contract_transaction_interface_from_directory(contract_dir: str, contract_name: Optional[str] = None) -> Type:
    """
    Load contract class from transaction interface stored in contract_dir

    :param contract_dir: directory with contract compilation output
    :param contract_name: contract name, only required if file contains multiple contracts
    :return: Contract class
    """
    contract_mod = load_transaction_interface_from_directory(contract_dir)
    return load_contract_transaction_interface_from_module(contract_mod, contract_name)


def deploy_contract(contract_dir: str, account, *args, contract_name: Optional[str] = None):
    """
    Deploy zkay contract in contract_dir using the given account and with specified constructor arguments.

    :param contract_dir: contract's compilation output directory
    :param account: Account from which to deploy the contract
    :param args: constructor arguments
    :param contract_name: contract name, only required if file contains multiple contracts
    :raise BlockChainError: if deployment fails
    :return: contract instance
    """
    c = load_contract_transaction_interface_from_directory(contract_dir, contract_name)
    return c.deploy(*args, user=account, project_dir=contract_dir)


def connect_to_contract_at(contract_dir: str, contract_address, account, contract_name: Optional[str] = None):
    """
    Connect with account to zkay contract at contract_address, with local files in contract_dir.

    :param contract_dir: contract's compilation output directory
    :param contract_address: blockchain address of the deployed contract
    :param account: account from which to connect (will be used as msg.sender for transactions)
    :param contract_name: contract name, only required if file contains multiple contracts
    :raise BlockChainError: if connection fails
    :raise IntegrityError: if integrity check fails
    :return: contract instance
    """
    c = load_contract_transaction_interface_from_directory(contract_dir, contract_name)
    return c.connect(address=contract_address, user=account, project_dir=contract_dir)


def collect_package_contents(contract_dir: str) -> List[str]:
    """
    Return list of relative paths of all files which should be part of the package for the contract in contract_dir.

    Raises an exception if contract.zkay, manifest.json or any of the files required by contract.zkay is missing.

    :param contract_dir: path to directory containing manifest and zkay file
    :raise FileNotFoundError: if any of the expected files is not present
    :return: list of relative paths (relative to contract_dir)
    """

    zkay_filename = os.path.join(contract_dir, 'contract.zkay')
    if not os.path.exists(zkay_filename):
        raise FileNotFoundError('contract.zkay not found in package')

    manifest_filename = os.path.join(contract_dir, 'manifest.json')
    if not os.path.exists(manifest_filename):
        raise FileNotFoundError('manifest.json not found in package')
    manifest = Manifest.load(contract_dir)

    files = ['contract.zkay', 'manifest.json']
    with open(zkay_filename) as f:
        verifier_names = get_verification_contract_names(f.read())
    with Manifest.with_manifest_config(manifest):
        gen_cls = generator_classes[cfg.snark_backend]
        files += [os.path.join(cfg.get_circuit_output_dir_name(v), k)
                  for k in gen_cls.get_vk_and_pk_filenames() for v in verifier_names]

    for f in files:
        path = os.path.join(contract_dir, f)
        if not os.path.exists(path) or not os.path.isfile(path):
            raise FileNotFoundError(f)
    return files


def package_zkay_contract(zkay_output_dir: str, output_filename: str):
    """Package zkay contract for distribution."""
    if not output_filename.endswith('.zkp'):
        output_filename += '.zkp'

    with print_step('Packaging for distribution'):
        files = collect_package_contents(zkay_output_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            for file in files:
                src = os.path.join(zkay_output_dir, file)
                dest = os.path.join(tmpdir, file)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(src, dest)
            shutil.make_archive(without_extension(output_filename), 'zip', tmpdir)
        os.rename(f'{without_extension(output_filename)}.zip', output_filename)


def extract_zkay_package(zkp_filename: str, output_dir: str):
    """
    Unpack and compile a zkay contract.

    :param zkp_filename: path to the packaged contract
    :param output_dir: directory where to unpack and compile the contract
    :raise Exception: if import fails
    """
    os.makedirs(output_dir)
    try:
        shutil.unpack_archive(zkp_filename, output_dir, format='zip')

        # Check if required files exist in package
        files = collect_package_contents(output_dir)

        # Check that no other files exist in package
        whitelist = {os.path.join(output_dir, file) for file in files}
        for dirpath, _, filenames in os.walk(output_dir):
            for file in filenames:
                if os.path.join(dirpath, file) not in whitelist:
                    raise ValueError(f'package contains illegal unexpected file {file}')

        zkay_filename = os.path.join(output_dir, 'contract.zkay')
        manifest = Manifest.load(output_dir)
        with Manifest.with_manifest_config(manifest):
            compile_zkay_file(zkay_filename, output_dir, import_keys=True)
    except Exception as e:
        # If there was an exception, the archive is not safe -> remove extracted contents
        print(f'Package {zkp_filename} is either corrupt or incompatible with this zkay version.')
        shutil.rmtree(output_dir)
        raise e


def _dump_to_output(content: str, output_dir: str, filename: str, dryrun_solc=False) -> str:
    """
    Dump 'content' into file 'output_dir/filename' and optionally check if it compiles error-free with solc.

    :raise SolcException: if dryrun_solc is True and there are compilation errors
    :return: dumped content as string
    """

    path = os.path.join(output_dir, filename)
    with open(path, 'w') as f:
        f.write(content)
    if dryrun_solc:
        check_compilation(path, show_errors=False)
    return content
