"""
This module defines pinned versions and is used internally to configure the concrete solc version to use
"""
import os
import sys

from semantic_version import NpmSpec, Version


class Versions:
    ZKAY_SOLC_VERSION_COMPATIBILITY = NpmSpec('^0.6.0')
    ZKAY_LIBRARY_SOLC_VERSION = '0.6.12'
    SOLC_VERSION = None

    # Read zkay version from VERSION file
    with open(os.path.join(os.path.realpath(os.path.dirname(__file__)), 'VERSION')) as f:
        ZKAY_VERSION = f.read().strip()

    @staticmethod
    def set_solc_version(version: str):
        version = version[1:] if version.startswith('v') else version

        import solcx
        from solcx.exceptions import SolcNotInstalled
        if version == 'latest':
            try:
                solcx.set_solc_version_pragma(Versions.ZKAY_SOLC_VERSION_COMPATIBILITY.expression, silent=True, check_new=False)
            except SolcNotInstalled:
                print('ERROR: No compatible solc version is installed.\n'
                      'Please use "zkay update-solc" to install the latest compatible solc version.')
                sys.exit(100)
        else:
            try:
                v = Version(version)
                if not Versions.ZKAY_SOLC_VERSION_COMPATIBILITY.match(v):
                    raise ValueError(f'Zkay only supports solc versions satisfying {Versions.ZKAY_SOLC_VERSION_COMPATIBILITY.expression}')
                solcx.set_solc_version(version, silent=True)
            except ValueError as e:
                raise ValueError(f'Invalid version string {version}\n{e}')
            except SolcNotInstalled:
                try:
                    solcx.install_solc(version)
                    solcx.set_solc_version(version, silent=True)
                except Exception as e:
                    print(f'ERROR: Error while trying to install solc version {version}\n{e.args}')
                    sys.exit(101)

        Versions.SOLC_VERSION = f"v{solcx.get_solc_version().truncate(level='patch')}"
