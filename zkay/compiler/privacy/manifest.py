import json
import os
from contextlib import contextmanager
from typing import ContextManager

from zkay.config import cfg
from zkay.utils.progress_printer import warn_print


class Manifest:
    """Static class, which holds the string keys of all supported zkay manifest keys """
    zkay_version = 'zkay-version'
    solc_version = 'solc-version'
    zkay_options = 'zkay-options'

    @staticmethod
    def load(project_dir):
        """Returned parsed manifest json file located in project dir."""
        with open(os.path.join(project_dir, 'manifest.json')) as f:
            j = json.loads(f.read())
        return j

    @staticmethod
    def import_manifest_config(manifest):
        # Check if zkay version matches
        if manifest[Manifest.zkay_version] != cfg.zkay_version:
            with warn_print():
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
