import json
import os
from contextlib import contextmanager
from typing import ContextManager

from zkay.config import cfg
from zkay.utils.progress_printer import colored_print, TermColor


class Manifest:
    """Static class, which holds the string keys of all supported zkay manifest keys """
    uuid = 'uuid'
    zkay_version = 'zkay-version'
    solc_version = 'solc-version'
    zkay_options = 'zkay-options'
    zkay_contract_filename = 'zkay-contract-file'
    contract_filename = 'contract-file'
    pki_lib = 'pki-lib'
    verify_lib = 'verify-lib'
    verifier_names = 'verifier-names'

    project_dir = 'project-dir'
    """This key is dynamically set at runtime, not part of the manifest file"""

    @staticmethod
    def load(project_dir):
        """Returned parsed manifest json file located in project dir."""
        with open(os.path.join(project_dir, 'manifest.json')) as f:
            j = json.loads(f.read())
            j[Manifest.project_dir] = project_dir
        return j

    @staticmethod
    def import_manifest_config(manifest):
        # Check if zkay version matches
        if manifest[Manifest.zkay_version] != cfg.zkay_version:
            with colored_print(TermColor.WARNING):
                print(
                    f'Zkay version in manifest ({manifest[Manifest.zkay_version]}) does not match current zkay version ({cfg.zkay_version})\n'
                    f'Compilation or integrity check with deployed bytecode might fail due to version differences')

        cfg.override_solc(manifest[Manifest.solc_version])
        cfg.import_compiler_settings(manifest[Manifest.zkay_options])

    @staticmethod
    @contextmanager
    def with_manifest_config(manifest) -> ContextManager:
        old_solc = cfg.solc_version
        old_settings = cfg.export_compiler_settings()
        try:
            Manifest.import_manifest_config(manifest)
            yield
        finally:
            cfg.override_solc(old_solc)
            cfg.import_compiler_settings(old_settings)
