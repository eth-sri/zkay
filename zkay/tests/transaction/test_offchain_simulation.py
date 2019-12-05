import importlib
import os
import shutil
import sys

from parameterized import parameterized_class

from zkay.compiler.privacy.zkay_frontend import compile_zkay
from zkay.examples.scenario import TransactionAssertion, Transaction
from zkay.examples.scenarios import all_scenarios
from zkay.tests.utils.test_examples import TestScenario

# get relevant paths
script_dir = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(script_dir, 'output')


@parameterized_class(('name', 'scenario'), all_scenarios)
class TestScenarios(TestScenario):

    def get_directory(self):
        d = os.path.join(output_dir, self.name)

        if os.path.isdir(d):
            shutil.rmtree(d)
        os.mkdir(d)

        return d

    def test_offchain_simulation(self):
        run_scenario(self)


def run_scenario(runner):
    c = runner.scenario.code()
    d = runner.get_directory()

    # Compile contract
    cg, code = compile_zkay(c, d, runner.scenario.filename)
    runner.assertIsNotNone(cg)
    runner.assertIsNotNone(code)

    # Import dynamically generated offchain code
    sys.path.append(d)
    oc = importlib.import_module('contract')
    sys.path.pop()

    # Create dummy users
    user_names = runner.scenario.users()
    user_addresses = oc.create_dummy_accounts(len(user_names))
    if isinstance(user_addresses, str):
        user_addresses = tuple([user_addresses])
    user_addresses = {name: address for name, address in zip(user_names, user_addresses)}

    # Deploy contract and connect all users
    users = {}
    deployment_transaction = runner.scenario.deployment_transaction()
    owner = deployment_transaction.user
    contract_address = None
    for user, address in user_addresses.items():
        if user == owner:
            if deployment_transaction.amount is None:
                contract = oc.deploy(*deployment_transaction.args, user=address)
            else:
                contract = oc.deploy(*deployment_transaction.args, user=address, value=deployment_transaction.amount)
            runner.assertIsNotNone(contract)
            contract_address = contract.address
            users[owner] = contract
            break
    assert contract_address is not None
    for user, address in user_addresses.items():
        if user != owner:
            users[user] = oc.connect(contract_address, user=address)
            runner.assertIsNotNone(users[user])
    del oc

    # Execute all transactions and check assertions
    transactions_and_assertions = runner.scenario.transactions_and_assertions()
    for trans_or_assert in transactions_and_assertions:
        if isinstance(trans_or_assert, TransactionAssertion):
            # Check assertion
            trans_or_assert.check_assertion(runner, users)
        else:
            assert isinstance(trans_or_assert, Transaction)
            # Execute transaction
            transact = getattr(users[trans_or_assert.user], trans_or_assert.name)
            if trans_or_assert.amount is None:
                receipt = transact(*trans_or_assert.args)
            else:
                receipt = transact(*trans_or_assert.args, value=trans_or_assert.amount)
            runner.assertIsNotNone(receipt)
