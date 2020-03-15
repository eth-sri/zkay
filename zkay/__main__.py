#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
from enum import IntEnum

import argcomplete
import argparse
import os

from argcomplete.completers import FilesCompleter, DirectoriesCompleter

from zkay.compiler.privacy.zkay_frontend import load_transaction_interface_from_directory, \
    load_contract_transaction_interface_from_module
from zkay.config_user import UserConfig
from zkay.transaction.interface import BlockChainError, IntegrityError
from zkay.transaction.offchain import ContractSimulator
from zkay.utils.progress_printer import fail_print, success_print


def parse_config_doc():
    import textwrap
    from typing import get_type_hints
    __ucfg = UserConfig()

    docs = {}
    for name, prop in vars(UserConfig).items():
        if name.startswith('_') or not isinstance(prop, property):
            continue
        t = get_type_hints(prop.fget)['return']
        doc = prop.__doc__
        choices = None
        if hasattr(__ucfg, f'_{name}_values'):
            choices = getattr(__ucfg, f'_{name}_values')
        default_val = getattr(__ucfg, name)
        docs[name] = (
            f"type: {t}\n\n"
            f"{textwrap.dedent(doc).strip()}\n\n"
            f"Default value: {default_val}", t, default_val, choices)
    return docs


def parse_arguments():
    class ShowSuppressedInHelpFormatter(argparse.RawTextHelpFormatter):
        def add_usage(self, usage, actions, groups, prefix=None):
            if usage is not argparse.SUPPRESS:
                actions = [action for action in actions if action.metavar != '<cfg_val>']
                args = usage, actions, groups, prefix
                self._add_item(self._format_usage, args)

    main_parser = argparse.ArgumentParser(prog='zkay')
    zkay_files = ('zkay', 'sol')
    zkay_package_files = ('zkp', )
    config_files = ('json', )

    msg = 'Path to local configuration file (defaults to "config.json" in cwd). ' \
          'This file (if it exists), overrides settings defined in the global configuration.'
    main_parser.add_argument('--config-file', default='config.json', metavar='<config_file>', help=msg).completer = FilesCompleter(config_files)

    # Shared 'config' parser
    config_parser = argparse.ArgumentParser(add_help=False)
    msg = 'These parameters can be used to override settings defined (and documented) in config_user.py'
    cfg_group = config_parser.add_argument_group(title='Configuration Options', description=msg)

    # Expose config_user.py options via command line arguments, they are supported in all parsers
    cfg_docs = parse_config_doc()

    def add_config_args(parser, arg_names):
        for name in arg_names:
            doc, t, defval, choices = cfg_docs[name]

            if t is bool:
                if defval:
                    parser.add_argument(f'--no-{name.replace("_", "-")}', dest=name, help=doc, action='store_false')
                else:
                    parser.add_argument(f'--{name.replace("_", "-")}', dest=name, help=doc, action='store_true')
            elif t is int:
                parser.add_argument(f'--{name.replace("_", "-")}', type=int, dest=name, metavar='<cfg_val>', help=doc)
            else:
                arg = parser.add_argument(f'--{name.replace("_", "-")}', dest=name, metavar='<cfg_val>', help=doc,
                                          choices=choices)
                if name.endswith('dir'):
                    arg.completer = DirectoriesCompleter()
    add_config_args(cfg_group, cfg_docs.keys())

    solc_version_help = 'zkay defaults to using the latest solc version of the major\n' \
          'solidity version supported by the current zkay version.\n\n' \
          'If you need to use a particular minor release (e.g. because \n' \
          'the latest release is broken or you need determinism for testing)\n' \
          'you can specify a particular solc version (e.g. v0.5.12) via this argument.'

    subparsers = main_parser.add_subparsers(title='actions', dest='cmd', required=True)

    # 'compile' parser
    compile_parser = subparsers.add_parser('compile', parents=[config_parser], help='Compile a zkay contract.', formatter_class=ShowSuppressedInHelpFormatter)
    msg = 'The directory to output the compiled contract to. Default: Current directory'
    compile_parser.add_argument('-o', '--output', default=os.getcwd(), help=msg, metavar='<output_directory>').completer = DirectoriesCompleter()
    compile_parser.add_argument('input', help='The zkay source file', metavar='<zkay_file>').completer = FilesCompleter(zkay_files)
    compile_parser.add_argument('--log', action='store_true', help='enable logging')
    compile_parser.add_argument('--solc-version', help=solc_version_help, metavar='<cfg_val>')

    # 'check' parser
    typecheck_parser = subparsers.add_parser('check', parents=[config_parser], help='Only type-check, do not compile.', formatter_class=ShowSuppressedInHelpFormatter)
    typecheck_parser.add_argument('input', help='The zkay source file', metavar='<zkay_file>').completer = FilesCompleter(zkay_files)
    typecheck_parser.add_argument('--solc-version', help=solc_version_help, metavar='<cfg_val>')

    # 'solify' parser
    msg = 'Output solidity code which corresponds to zkay code with all privacy features and comments removed, ' \
          'useful in conjunction with analysis tools which operate on solidity code.)'
    solify_parser = subparsers.add_parser('solify', parents=[config_parser], help=msg, formatter_class=ShowSuppressedInHelpFormatter)
    solify_parser.add_argument('input', help='The zkay source file', metavar='<zkay_file>').completer = FilesCompleter(zkay_files)

    # 'export' parser
    export_parser = subparsers.add_parser('export', parents=[config_parser], help='Package a compiled zkay contract.', formatter_class=ShowSuppressedInHelpFormatter)
    msg = 'Output filename. Default: ./contract.zkp'
    export_parser.add_argument('-o', '--output', default='contract.zkp', help=msg, metavar='<output_filename>').completer = FilesCompleter(zkay_package_files)
    msg = 'Directory with the compilation output of the contract which should be packaged.'
    export_parser.add_argument('input', help=msg, metavar='<zkay_compilation_output_dir>').completer = DirectoriesCompleter()

    # 'import' parser
    import_parser = subparsers.add_parser('import', parents=[config_parser], help='Unpack a packaged zkay contract.', formatter_class=ShowSuppressedInHelpFormatter)
    msg = 'Directory where the contract should be unpacked to. Default: Current Directory'
    import_parser.add_argument('-o', '--output', default=os.getcwd(), help=msg, metavar='<target_directory>').completer = DirectoriesCompleter()
    msg = 'Contract package to unpack.'
    import_parser.add_argument('input', help=msg, metavar='<zkay_package_file>').completer = FilesCompleter(zkay_package_files)

    # 'run, deploy and connect' parsers
    interact_parser = argparse.ArgumentParser(add_help=False)
    msg = 'Directory with the compilation output of the contract with which you want to interact.'
    interact_parser.add_argument('input', help=msg, metavar='<zkay_compilation_output_dir>').completer = DirectoriesCompleter()
    interact_parser.add_argument('--log', action='store_true', help='enable logging')
    interact_parser.add_argument('--account', help='Sender blockchain address', metavar='<address>')

    subparsers.add_parser('run', parents=[interact_parser, config_parser],
                          help='Enter transaction shell for a compiled zkay contract.',
                          formatter_class=ShowSuppressedInHelpFormatter)

    deploy_parser = subparsers.add_parser('deploy', parents=[interact_parser, config_parser],
                                          help='Deploy contract with arguments and enter shell.',
                                          formatter_class=ShowSuppressedInHelpFormatter)
    deploy_parser.add_argument('constructor_args', nargs='*', help='Constructor arguments', metavar='<args>...')

    connect_parser = subparsers.add_parser('connect', parents=[interact_parser, config_parser],
                                          help='Connect to contract at address and enter shell.',
                                          formatter_class=ShowSuppressedInHelpFormatter)
    connect_parser.add_argument('address', help='Blockchain address of deployed contract', metavar='<address>')

    # Common deploy libs parameters
    deploy_libs_parser = argparse.ArgumentParser(add_help=False)
    msg = 'Address of the account to use for deploying the library contracts. ' \
          'Its ethereum keys must be hosted in the specified node and sufficient funds ' \
          'to cover the deployment costs must be available. ' \
          'WARNING: This account will be charged with the deployment costs.'
    deploy_libs_parser.add_argument('account', metavar='<deployer account ethereum address>', help=msg)

    # 'deploy-pki' parser
    dpki_parser = subparsers.add_parser('deploy-pki', parents=[deploy_libs_parser],
                                        help='Manually deploy global pki contract compatible with a particular crypto backend to a blockchain')
    add_config_args(dpki_parser, {'crypto_backend', 'blockchain_backend', 'blockchain_node_uri'})

    # 'deploy-crypto-libs' parser
    dclibs_parser = subparsers.add_parser('deploy-crypto-libs', parents=[deploy_libs_parser],
                                          help='Manually deploy proving-scheme specific crypto libraries (if any needed) to a blockchain')
    add_config_args(dclibs_parser, {'proving_scheme', 'blockchain_backend', 'blockchain_node_uri'})

    # parse
    argcomplete.autocomplete(main_parser, always_complete_options=False)
    a = main_parser.parse_args()
    return a


def main():
    # parse arguments
    a = parse_arguments()

    from pathlib import Path

    import zkay.compiler.privacy.zkay_frontend as frontend
    from zkay import my_logging
    from zkay.config import cfg
    from zkay.utils.helpers import read_file, save_to_file
    from zkay.errors.exceptions import ZkayCompilerError
    from zkay.my_logging.log_context import log_context
    from zkay.zkay_ast.process_ast import get_processed_ast, get_parsed_ast_and_fake_code

    # Load configuration files
    try:
        cfg.load_configuration_from_disk(a.config_file)
    except Exception as e:
        with fail_print():
            print(f"ERROR: Failed to load configuration files\n{e}")
            exit(42)

    # Support for overriding any user config setting via command line
    # The evaluation order for configuration loading is:
    # Default values in config.py -> Site config.json -> user config.json -> local config.json -> cmdline arguments
    # Settings defined at a later stage override setting values defined at an earlier stage
    override_dict = {}
    for name in vars(UserConfig):
        if name[0] != '_' and hasattr(a, name):
            val = getattr(a, name)
            if val is not None:
                override_dict[name] = val
    cfg.override_defaults(override_dict)

    if a.cmd in ['deploy-pki', 'deploy-crypto-libs']:
        import tempfile
        from zkay.compiler.privacy import library_contracts
        from zkay.transaction.runtime import Runtime
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                with cfg.library_compilation_environment():
                    if a.cmd == 'deploy-pki':
                        file = save_to_file(tmpdir, f'{cfg.pki_contract_name}.sol', library_contracts.get_pki_contract())
                        addr = Runtime.blockchain().deploy_solidity_contract(file, cfg.pki_contract_name, a.account)
                        print(f'Deployed pki contract at: {addr}')
                    else:
                        file = save_to_file(tmpdir, 'verify_libs.sol', library_contracts.get_verify_libs_code())
                        for lib in cfg.external_crypto_lib_names:
                            addr = Runtime.blockchain().deploy_solidity_contract(file, lib, a.account)
                            print(f'Deployed crypto library {lib} at: {addr}')
            except Exception as e:
                with fail_print():
                    print(f"ERROR: Deployment failed\n{e}")
    else:
        # Solc version override
        if hasattr(a, 'solc_version') and a.solc_version is not None:
            try:
                cfg.override_solc(a.solc_version)
            except ValueError as e:
                with fail_print():
                    print(f'Error: {e}')
                exit(10)

        input_path = Path(a.input)
        if not input_path.exists():
            with fail_print():
                print(f'Error: input file \'{input_path}\' does not exist')
            exit(1)

        if a.cmd == 'check':
            # only type-check
            print(f'Type checking file {input_path.name}:')

            code = read_file(str(input_path))
            try:
                get_processed_ast(code)
            except ZkayCompilerError as e:
                with fail_print():
                    print(f'{e}')
                exit(3)
        elif a.cmd == 'solify':
            was_unit_test = cfg.is_unit_test
            cfg._is_unit_test = True  # Suppress other output
            try:
                _, fake_code = get_parsed_ast_and_fake_code(read_file(str(input_path)))
                print(fake_code)
            except ZkayCompilerError as e:
                with fail_print():
                    print(f'{e}')
                exit(3)
            finally:
                cfg._is_unit_test = was_unit_test
            exit(0)
        elif a.cmd == 'compile':
            # create output directory
            output_dir = Path(a.output).absolute()
            if not output_dir.exists():
                os.makedirs(output_dir)
            elif not output_dir.is_dir():
                with fail_print():
                    print(f'Error: \'{output_dir}\' is not a directory')
                exit(2)

            # Enable logging
            if a.log:
                log_file = my_logging.get_log_file(filename='compile', include_timestamp=False, label=None)
                my_logging.prepare_logger(log_file)

            # only type-check
            print(f'Compiling file {input_path.name}:')

            # compile
            with log_context('inputfile', os.path.basename(a.input)):
                try:
                    frontend.compile_zkay_file(str(input_path), str(output_dir))
                except ZkayCompilerError as e:
                    with fail_print():
                        print(f'{e}')
                    exit(3)
        elif a.cmd == 'import':
            # create output directory
            output_dir = Path(a.output).absolute()
            if output_dir.exists():
                with fail_print():
                    print(f'Error: \'{output_dir}\' already exists')
                exit(2)

            try:
                frontend.extract_zkay_package(str(input_path), str(output_dir))
            except ZkayCompilerError as e:
                with fail_print():
                    print(f"ERROR while compiling unpacked zkay contract.\n{e}")
                exit(3)
            except Exception as e:
                with fail_print():
                    print(f"ERROR while unpacking zkay contract\n{e}")
                exit(5)
        elif a.cmd == 'export':
            output_filename = Path(a.output).absolute()
            os.makedirs(output_filename.parent, exist_ok=True)
            try:
                frontend.package_zkay_contract(str(input_path), str(output_filename))
            except Exception as e:
                with fail_print():
                    print(f"ERROR while exporting zkay contract\n{e}")
                exit(4)
        elif a.cmd in ['run', 'deploy', 'connect']:
            def echo_only_simple_expressions(e):
                if isinstance(e, (bool, int, str, list, IntEnum)):
                    print(e)

            # Enable logging
            if a.log:
                log_file = my_logging.get_log_file(filename=f'transactions_{input_path.name}', include_timestamp=True, label=None)
                my_logging.prepare_logger(log_file)

            contract_dir = str(input_path.absolute())
            ContractSimulator.use_config_from_manifest(contract_dir)
            if a.account is not None:
                me = a.account
            else:
                me = ContractSimulator.default_address()
                if me is not None:
                    me = me.val

            import code
            import sys
            if a.cmd == 'run':
                # Dynamically load module and replace globals with module globals
                contract_mod = load_transaction_interface_from_directory(contract_dir)
                contract_mod.me = me
                sys.displayhook = echo_only_simple_expressions
                code.interact(local=contract_mod.__dict__)
            else:
                cmod = load_transaction_interface_from_directory(contract_dir)
                c = load_contract_transaction_interface_from_module(cmod)
                if a.cmd == 'deploy':
                    from ast import literal_eval
                    cargs = a.constructor_args
                    args = []
                    for arg in cargs:
                        try:
                            val = literal_eval(arg)
                        except Exception:
                            val = arg
                        args.append(val)
                    try:
                        c_inst = c.deploy(*args, user=me, project_dir=contract_dir)
                    except (ValueError, TypeError) as e:
                        with fail_print():
                            print(f'ERROR invalid arguments.\n{e}\n\nExpected contructor signature: ', end='')
                            if hasattr(c, 'constructor'):
                                from inspect import signature
                                sig = str(signature(c.constructor))
                                sig = sig[5:] if not sig[5:].startswith(",") else sig[7:] # without self
                                print(f'({sig}')
                            else:
                                print('()')
                            exit(11)
                    except Exception as e:
                        with fail_print():
                            print(f'ERROR: failed to deploy contract\n{e}')
                            exit(12)
                elif a.cmd == 'connect':
                    try:
                        c_inst = c.connect(address=a.address, user=me, project_dir=contract_dir)
                    except Exception as e:
                        with fail_print():
                            print(f'ERROR: failed to connect to contract\n{e}')
                            exit(13)
                else:
                    raise ValueError(f'unexpected command {a.cmd}')

                contract_scope = {name: getattr(c_inst, name) for name in dir(c_inst)
                                  if (name != 'constructor' and hasattr(getattr(c_inst, name), '_can_be_external') and getattr(c_inst, name)._can_be_external)
                                      or name == 'api'}
                contract_scope['me'] = me
                contract_scope['help'] = lambda o=None: help(o) if o is not None else ContractSimulator.reduced_help(c)
                sys.displayhook = echo_only_simple_expressions
                code.interact(local=contract_scope)
            exit(0)
        else:
            raise NotImplementedError(a.cmd)

        with success_print():
            print("Finished successfully")


if __name__ == '__main__':
    main()
