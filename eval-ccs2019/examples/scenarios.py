import os
import re
import my_logging
from distutils import dir_util
from typing import Dict, List
from shutil import copyfile

from my_logging.log_context import log_context, add_log_context, remove_log_context
from utils.helpers import read_file, save_to_file, prepend_to_lines
from transaction.run import get_runner, run_function, list_to_str


script_dir = os.path.dirname(os.path.realpath(__file__))
template = os.path.join(script_dir, '..', 'app-template')


class ScenarioGenerator:

    def __init__(self, directory: str, filename: str, keys: Dict[str, int]):
        add_log_context('inputfileTx', filename)
        # locations
        self.directory = directory
        self.filename = filename
        self.output_directory = os.path.join(directory, 'compiled')
        self.code_file = os.path.join(directory, filename)

        # copy template to current directory
        self.scenario_directory = os.path.join(self.directory, 'scenario')
        dir_util.copy_tree(template, self.scenario_directory)
        self.scenario_js_file = os.path.join(self.scenario_directory, 'scenario.js')
        self.scenario_js = read_file(self.scenario_js_file)
        self.deploy_js_file = os.path.join(self.scenario_directory, 'migrations', '2_deploy_contracts.js')
        self.deploy_js = read_file(self.deploy_js_file)

        # copy contracts
        for filename in os.listdir(self.output_directory):
            if filename.endswith('.sol'):
                source = os.path.join(self.output_directory, filename)
                target = os.path.join(self.scenario_directory, 'contracts', filename)
                copyfile(source, target)

        # prepare logging
        log_file = my_logging.get_log_file(None, self.scenario_directory, 'transactions', False)
        my_logging.prepare_logger(log_file)

        # prepare runner
        self.r = get_runner(self.output_directory, self.code(), self.name(), keys)

        # others
        self.transactions = []
        self.set_contract_name()
        self.set_accounts(keys)
        self.set_pk_announce(keys)
        self.set_contract_fetch()
        self.set_verifiers()

        self.n_calls = 0

    def code(self):
        return read_file(self.code_file)

    def name(self):
        c = self.code()
        m = re.search('contract ([^ {]*)', c)
        return m.group(1)

    def set_contract_name(self):
        contract_name = f'helpers.contract_name = "{self.name()}";'
        self.scenario_js = self.scenario_js.replace('$CONTRACT_NAME', contract_name)
        self.deploy_js = self.deploy_js.replace('$CONTRACT_NAME', contract_name)

    def set_contract_fetch(self):
        contract_fetch = f'var contract = artifacts.require("{self.name()}");'
        self.scenario_js = self.scenario_js.replace('$CONTRACT_FETCH', contract_fetch)

    def set_pk_announce(self, keys: Dict[str, int]):
        lines = []
        for k, v in keys.items():
            lines += [f'await helpers.tx(genPublicKeyInfrastructure, "announcePk", [{v}], {k});']
        lines = '\n'.join(lines)
        lines = prepend_to_lines(lines, '\t')
        self.scenario_js = self.scenario_js.replace('$PK_ANNOUNCE', lines)

    def set_accounts(self, keys: Dict[str, int]):
        lines = []
        for i, k in enumerate(keys.keys()):
            lines += [f'var {k} = accounts[{i}];']
        lines = '\n'.join(lines)
        lines = prepend_to_lines(lines, '\t')
        self.scenario_js = self.scenario_js.replace('$ACCOUNTS', lines)

    def set_verifiers(self):
        verifiers_fetch = []
        verifiers_deploy = []
        verifiers_wait = []
        for c in self.r.compiler_information.used_contracts:
            if 'PublicKeyInfrastructure' not in c.contract_name:
                verifiers_fetch += [f'var {c.state_variable_name} = artifacts.require("{c.contract_name}");']
                verifiers_deploy += [f'await deployer.link(pairing, {c.state_variable_name});\nawait deployer.link(bn256g2, {c.state_variable_name});\nawait helpers.deploy(web3, deployer, {c.state_variable_name}, [], accounts[0]);']
                verifiers_wait += [f'{c.state_variable_name} = await {c.state_variable_name}.deployed();']
        verifiers_fetch = prepend_to_lines('\n'.join(verifiers_fetch), '\t')
        verifiers_deploy = prepend_to_lines('\n'.join(verifiers_deploy), '\t')
        verifiers_wait = prepend_to_lines('\n'.join(verifiers_wait), '\t')
        self.deploy_js = self.deploy_js \
            .replace('$VERIFIERS_FETCH', verifiers_fetch) \
            .replace('$VERIFIERS_DEPLOY', verifiers_deploy)
        self.scenario_js = self.scenario_js.replace('$VERIFIERS_FETCH', verifiers_fetch)
        self.scenario_js = self.scenario_js.replace('$VERIFIERS_WAIT', verifiers_wait)

    def run_function(self, function_name: str, me: str, args: List):
        with log_context('nCalls', self.n_calls):
            self.n_calls += 1
            with log_context('runFunction', function_name):
                real_args = run_function(self.r, function_name, me, args)

                args_str = list_to_str(args)
                real_args_str = list_to_str(real_args)

                if function_name == 'constructor':
                    t = f'// {function_name}({args_str})\nargs = [{real_args_str}];\nlet contract_instance = await helpers.deploy_x(web3, contract, args, {me});'
                    t = prepend_to_lines(t, '\t')
                    self.scenario_js = self.scenario_js.replace('$CONTRACT_DEPLOY', t)
                else:
                    t = f'// {function_name}({args_str})\nargs = [{real_args_str}];\nawait helpers.tx(contract_instance, "{function_name}", args, {me});'
                    t = prepend_to_lines(t, '\t')
                    self.transactions += [t]

    def finalize(self):
        transactions = '\n\n'.join(self.transactions)
        self.scenario_js = self.scenario_js.replace('$TRANSACTIONS', transactions)

        save_to_file(None, self.scenario_js_file, self.scenario_js)
        save_to_file(None, self.deploy_js_file, self.deploy_js)
        remove_log_context('inputfileTx')
