#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argcomplete, argparse
from argcomplete.completers import FilesCompleter, DirectoriesCompleter
import os
from zkay.utils.helpers import read_file
from zkay.config_user import UserConfig
__ucfg = UserConfig()


def parse_config_doc(config_py_filename: str):
    import re
    import textwrap

    config_contents = read_file(config_py_filename)
    docs = {}
    reg_template = r'^\s*self\.{} *(?P<type>:[^\n=]*)?=(?P<default>(?:.|[\n\r])*?(?="""))(?:"""(?P<doc>(?:.|[\n\r])*?(?=""")))'
    for copt in vars(__ucfg):
        if not copt.startswith('_'):
            match = re.search(reg_template.format(copt), config_contents, re.MULTILINE)
            match_groups = match.groupdict()
            docs[copt] = (f"type: {textwrap.dedent(match_groups['type']).strip()}" if match_groups['type'] is not None else '',
                          textwrap.dedent(match_groups['doc']).strip() if match_groups['doc'] is not None else '',
                          f"Default value: {textwrap.dedent(match_groups['default']).strip()}" if match_groups['default'] is not None else '')
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
    zkay_package_files = ('*.zkp', )

    subparsers = main_parser.add_subparsers(title='actions', dest='cmd', required=True)

    config_parser = argparse.ArgumentParser(add_help=False)
    cfg_group = config_parser.add_argument_group(title='Configuration Options', description='These parameters can be used to override settings defined (and documented) in config.py')

    # Expose config.py user options, they are supported in all parsers
    cfg_docs = parse_config_doc(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config_user.py'))
    for copt in vars(__ucfg):
        if not copt.startswith('_'):
            msg = '\n\n'.join(cfg_docs[copt])
            cfg_group.add_argument(f'--{copt}', dest=copt, metavar='<cfg_val>', help=msg)

    # 'compile' parser
    compile_parser = subparsers.add_parser('compile', parents=[config_parser], help='Compile a zkay contract.', formatter_class=ShowSuppressedInHelpFormatter)
    msg = 'The directory to output the compiled contract to. Default: Current directory'
    a = compile_parser.add_argument('-o', '--output', default=os.getcwd(), help=msg, metavar='<output_directory>').completer = DirectoriesCompleter()
    compile_parser.add_argument('input', help='The zkay source file', metavar='<zkay_file>').completer = FilesCompleter(zkay_files)

    # 'check' parser
    typecheck_parser = subparsers.add_parser('check', parents=[config_parser], help='Only type-check, do not compile.', formatter_class=ShowSuppressedInHelpFormatter)
    typecheck_parser.add_argument('input', help='The zkay source file', metavar='<zkay_file>').completer = FilesCompleter(zkay_files)

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

    # parse
    argcomplete.autocomplete(main_parser, always_complete_options=False)
    a = main_parser.parse_args()
    return a


def main():
    # parse arguments
    a = parse_arguments()

    from pathlib import Path
    from ast import literal_eval

    from zkay import my_logging
    from zkay.config import cfg
    from zkay.compiler.privacy.zkay_frontend import compile_zkay_file
    from zkay.errors.exceptions import ZkayCompilerError
    from zkay.my_logging.log_context import log_context
    from zkay.utils.progress_printer import TermColor, colored_print
    from zkay.zkay_ast.process_ast import get_processed_ast, get_parsed_ast_and_fake_code

    # Support for overriding any user config setting via command line
    override_dict = {}
    for copt in vars(cfg):
        if hasattr(a, copt) and getattr(a, copt) is not None:
            v = getattr(a, copt).strip()
            try:
                val = literal_eval(v)  # Try to interpret type
            except ValueError:
                val = v  # It is a string
            override_dict[copt] = val
    cfg.override_defaults(override_dict)

    if a.cmd in ['compile', 'check', 'solify']:
        input_file = Path(a.input)
        if not input_file.exists():
            with colored_print(TermColor.FAIL):
                print(f'Error: input file \'{input_file}\' does not exist')
            exit(1)

        if a.cmd == 'check':
            # only type-check
            print(f'Type checking file {input_file.name}:')

            code = read_file(str(input_file))
            try:
                get_processed_ast(code)
            except ZkayCompilerError as e:
                with colored_print(TermColor.FAIL):
                    print(f'{e}')
                exit(3)
        elif a.cmd == 'solify':
            was_unit_test = cfg.is_unit_test
            cfg._is_unit_test = True  # Suppress other output
            try:
                _, fake_code = get_parsed_ast_and_fake_code(read_file(str(input_file)))
                print(fake_code)
            finally:
                cfg._is_unit_test = was_unit_test
            exit(0)
        else:
            # create output directory
            output_dir = Path(a.output).absolute()
            if not output_dir.exists():
                os.mkdir(output_dir)
            elif not output_dir.is_dir():
                with colored_print(TermColor.FAIL):
                    print(f'Error: \'{output_dir}\' is not a directory')
                exit(2)

            # create log directory
            log_file = my_logging.get_log_file(filename='compile', parent_dir=str(output_dir), include_timestamp=False, label=None)
            my_logging.prepare_logger(log_file)

            # only type-check
            print(f'Compiling file {input_file.name}:')

            # compile
            with log_context('inputfile', os.path.basename(a.input)):
                try:
                    compile_zkay_file(str(input_file), str(output_dir))
                except ZkayCompilerError as e:
                    with colored_print(TermColor.FAIL):
                        print(f'{e}')
                    exit(3)

    with colored_print(TermColor.OKGREEN):
        print("Finished successfully")


if __name__ == '__main__':
    main()
