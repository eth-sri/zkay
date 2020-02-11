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
