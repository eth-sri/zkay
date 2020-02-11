"""
This module exposes functionality to compile and package zkay code
"""

import json
import os
import pathlib
import re
import shutil
import tempfile
import uuid
from copy import deepcopy
from typing import Tuple, List

from zkay import my_logging
from zkay.compiler.privacy import library_contracts
from zkay.compiler.privacy.circuit_generation.backends.jsnark_generator import JsnarkGenerator
from zkay.compiler.privacy.circuit_generation.circuit_generator import CircuitGenerator
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.manifest import Manifest
from zkay.compiler.privacy.offchain_compiler import PythonOffchainVisitor
from zkay.compiler.privacy.proving_scheme.backends.gm17 import ProvingSchemeGm17
from zkay.compiler.privacy.proving_scheme.proving_scheme import ProvingScheme
from zkay.compiler.privacy.transformer.zkay_contract_transformer import transform_ast
from zkay.compiler.solidity.compiler import check_compilation, SolcException
from zkay.config import cfg
from zkay.utils.helpers import read_file, lines_of_code, without_extension
from zkay.utils.progress_printer import print_step
from zkay.utils.timer import time_measure
from zkay.zkay_ast.process_ast import get_processed_ast, ParseExeception, PreprocessAstException, TypeCheckException


def compile_zkay_file(input_file_path: str, output_dir: str, import_keys: bool = False):
    """
    Parse, type-check and compile the given zkay contract file.

    :param input_file_path: path to the zkay contract file
    :param output_dir: path to a directory where the compilation output should be generated
    :param import_keys: if false, zk-snark of all modified circuits will be generated during compilation
                        if true, zk-snark keys for all circuits are expected to be already present in the output directory,
                                 and the compilation will use the provided keys to generate the verification contracts
                        This option is mostly used internally when connecting to a zkay contract provided by a 3rd-party
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
        cg, _ = compile_zkay(code, output_dir, without_extension(filename), import_keys)


def compile_zkay(code: str, output_dir: str, output_filename_without_ext: str, import_keys: bool = False) -> Tuple[CircuitGenerator, str]:
    """
    Parse, type-check and compile the given zkay code.

    :param code: zkay code to compile
    :param output_dir: path to a directory where the compilation output should be generated
    :param output_filename_without_ext: stem of the desired output solidity contract filename
    :param import_keys: if false, zk-snark of all modified circuits will be generated during compilation
                        if true, zk-snark keys for all circuits are expected to be already present in the output directory,
                                 and the compilation will use the provided keys to generate the verification contracts
                        This option is mostly used internally when connecting to a zkay contract provided by a 3rd-party
    """

    # Copy zkay code to output
    zkay_filename = f'{output_filename_without_ext}.zkay'
    if import_keys and not os.path.exists(os.path.join(output_dir, zkay_filename)):
        raise RuntimeError('Zkay file is expected to already be in the output directory when importing keys')
    elif not import_keys:
        _dump_to_output(code, output_dir, zkay_filename)

    # Type checking
    try:
        ast = get_processed_ast(code)
    except (ParseExeception, PreprocessAstException, TypeCheckException, SolcException) as e:
        if cfg.is_unit_test:
            raise e
        else:
            exit(3)

    # Contract transformation
    with print_step("Transforming zkay -> public contract"):
        ast, circuits = transform_ast(deepcopy(ast))

    # Dump libraries
    with print_step("Write library contract files"):
        # Write pki contract
        _dump_to_output(library_contracts.get_pki_contract(), output_dir, f'{cfg.pki_contract_name}.sol', dryrun_solc=True)

        # Write library contract
        _dump_to_output(library_contracts.get_verify_libs_code(), output_dir, ProvingScheme.verify_libs_contract_filename, dryrun_solc=True)

    # Write public contract file
    with print_step('Write public solidity code'):
        output_filename = f'{output_filename_without_ext}.sol'
        solidity_code_output = _dump_to_output(ast.code(), output_dir, output_filename)

    # Get all circuit helpers for the transformed contract
    circuits: List[CircuitHelper] = list(circuits.values())

    # Generate offchain simulation code (transforms transactions, interface to deploy and access the zkay contract)
    offchain_simulation_code = PythonOffchainVisitor(circuits).visit(ast)
    _dump_to_output(offchain_simulation_code, output_dir, 'contract.py')

    # Instantiate proving scheme and circuit generator
    ps, cg = _get_proving_scheme_and_generator(output_dir, circuits)

    # Generate manifest
    if not import_keys:
        with print_step("Writing manifest file"):
            manifest = {
                Manifest.uuid: uuid.uuid1().hex,
                Manifest.zkay_version: cfg.zkay_version,
                Manifest.solc_version: cfg.solc_version,
                Manifest.zkay_options: cfg.serialize(),
                Manifest.zkay_contract_filename: zkay_filename,
                Manifest.contract_filename: output_filename,
                Manifest.pki_lib: f'{cfg.pki_contract_name}.sol',
                Manifest.verify_lib: ProvingScheme.verify_libs_contract_filename,
                Manifest.verifier_names: {
                    f'{cc.fct.parent.idf.name}.{cc.fct.name}': cc.verifier_contract_type.code() for cc in
                    cg.circuits_to_prove
                }
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


def package_zkay(zkay_input_filename: str, cg: CircuitGenerator):
    """Package zkay contract for distribution."""

    with print_step('Packaging for distribution'):
        # create archive with zkay code + all verification and prover keys
        root = pathlib.Path(cg.output_dir)
        infile = pathlib.Path(zkay_input_filename)
        manifestfile = root.joinpath("manifest.json")
        filenames = [pathlib.Path(p) for p in cg.get_all_key_paths()]
        for p in filenames + [infile, manifestfile]:
            if not p.exists():
                raise FileNotFoundError()

        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copyfile(infile, os.path.join(tmpdir, infile.name))
            shutil.copyfile(manifestfile, os.path.join(tmpdir, manifestfile.name))
            for p in filenames:
                pdir = os.path.join(tmpdir, p.relative_to(root).parent)
                if not os.path.exists(pdir):
                    os.makedirs(pdir)
                shutil.copyfile(p.absolute(), os.path.join(tmpdir, p.relative_to(root)))

            output_basename = infile.name.replace('.sol', '')

            shutil.make_archive(os.path.join(cg.output_dir, output_basename), 'zip', tmpdir)

        os.rename(os.path.join(cg.output_dir, f'{output_basename}.zip'), os.path.join(cg.output_dir, f'{output_basename}.zkpkg'))


def import_pkg(filename: str):
    pass


def _dump_to_output(content: str, output_dir: str, filename: str, dryrun_solc=False) -> str:
    """
    Dump 'content' into file 'output_dir/filename' and optionally check if it compiles error-free with solc.

    :return: dumped content as string
    """

    path = os.path.join(output_dir, filename)
    with open(path, 'w') as f:
        f.write(content)
    if dryrun_solc:
        check_compilation(path, show_errors=False)
    return content


def _get_proving_scheme_and_generator(output_dir: str, circuits: List[CircuitHelper]) -> Tuple[ProvingScheme, CircuitGenerator]:
    """Return proving scheme and circuit generator instances based on backends selected in config."""
    if True:
        ps = ProvingSchemeGm17()

    if cfg.snark_backend == 'jsnark':
        cg = JsnarkGenerator(circuits, ps, output_dir)
    else:
        raise ValueError(f"Selected invalid backend {cfg.snark_backend}")

    return ps, cg
