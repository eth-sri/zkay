import importlib
import os
import shutil
import sys
import unittest
from contextlib import nullcontext

from parameterized import parameterized_class

from zkay.compiler.privacy.zkay_frontend import compile_zkay
from zkay.config import cfg
from zkay.examples.scenario import TransactionAssertion, Transaction
from zkay.examples.example_scenarios import all_scenarios, enc_scenarios, get_scenario
from zkay.tests.utils.test_examples import TestScenarios
from zkay.transaction.runtime import Runtime

# get relevant paths
from zkay.utils.helpers import without_extension

script_dir = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(script_dir, 'output')


class TestOffchainBase(TestScenarios):
    def get_directory(self, suffix: str, use_cache: bool):
        d = os.path.join(output_dir, f'{self.name}{suffix}')

        if os.path.isdir(d) and not use_cache:
            shutil.rmtree(d)
        if not os.path.isdir(d):
            os.mkdir(d)
            with open(os.path.join(d, '__init__.py'), 'w'):
                pass

        return d

    def run_scenario(self, *, suffix: str = '', use_cache: bool = False):
        Runtime.reset()

        c = self.scenario.code()
        d = self.get_directory(suffix, use_cache)

        # Compile contract
        cg, code = compile_zkay(c, d, without_extension(self.scenario.filename))
        self.assertIsNotNone(cg)
        self.assertIsNotNone(code)

        # Import dynamically generated offchain code
        sys.path.append(output_dir)
        oc = importlib.import_module(f'{self.name}{suffix}.contract')
        importlib.reload(oc)
        sys.path.pop()

        # Create dummy users
        user_names = self.scenario.users()
        user_addresses = oc.create_dummy_accounts(len(user_names))
        if isinstance(user_addresses, str):
            user_addresses = tuple([user_addresses])
        user_addresses = {name: address for name, address in zip(user_names, user_addresses)}

        # Deploy contract and connect all users
        users = {}
        deployment_transaction = self.scenario.deployment_transaction()
        owner = deployment_transaction.user
        contract_address = None
        for user, address in user_addresses.items():
            if user == owner:
                if deployment_transaction.amount is None:
                    contract = oc.deploy(*deployment_transaction.args, user=address)
                else:
                    contract = oc.deploy(*deployment_transaction.args, user=address,
                                         value=deployment_transaction.amount)
                self.assertIsNotNone(contract)
                contract_address = contract.address
                users[owner] = contract
                break
        assert contract_address is not None
        for user, address in user_addresses.items():
            if user != owner:
                users[user] = oc.connect(contract_address, user=address)
                self.assertIsNotNone(users[user])
        del oc
        importlib.invalidate_caches()

        # Execute all transactions and check assertions
        transactions_and_assertions = self.scenario.transactions_and_assertions()
        for trans_or_assert in transactions_and_assertions:
            if isinstance(trans_or_assert, TransactionAssertion):
                # Check assertion
                trans_or_assert.check_assertion(self, users)
            else:
                assert isinstance(trans_or_assert, Transaction)
                exception = trans_or_assert.expected_exception
                with nullcontext() if exception is None else self.assertRaises(exception):
                    # Execute transaction
                    transact = getattr(users[trans_or_assert.user], trans_or_assert.name)
                    args = [users[user].user_addr.val if user in users else user for user in trans_or_assert.args]
                    if trans_or_assert.amount is None:
                        receipt = transact(*args)
                    else:
                        receipt = transact(*args, value=trans_or_assert.amount)
                    self.assertIsNotNone(receipt)

        if not use_cache:
            shutil.rmtree(d)


#@parameterized_class(('name', 'scenario'), get_scenario(''))
@parameterized_class(('name', 'scenario'), all_scenarios)
class TestOffchainDummyEnc(TestOffchainBase):
    @unittest.skipIf(False, "No reason")
    def test_offchain_simulation_dummy(self):
        old = cfg.crypto_backend
        cfg.crypto_backend = 'dummy'
        self.run_scenario()
        cfg.crypto_backend = old


@parameterized_class(('name', 'scenario'), get_scenario('enctest.py'))
class TestOffchainWithHashing(TestOffchainBase):
    @unittest.skipIf(False, "No reason")
    def test_offchain_simulation_dummy_with_hashing(self):
        old = cfg.crypto_backend
        old_sh = cfg.should_use_hash
        cfg.crypto_backend = 'dummy'
        cfg.should_use_hash = lambda _: True
        self.run_scenario(suffix='WithHashing')
        cfg.should_use_hash = old_sh
        cfg.crypto_backend = old


@parameterized_class(('name', 'scenario'), enc_scenarios)
class TestOffchainRsaPkcs15Enc(TestOffchainBase):
    @unittest.skipIf(False or 'ZKAY_SKIP_REAL_ENC_TESTS' in os.environ and os.environ['ZKAY_SKIP_REAL_ENC_TESTS'] == '1', 'real encryption tests disabled')
    def test_offchain_simulation_rsa_pkcs_15(self):
        old = cfg.crypto_backend
        old_sh = cfg.should_use_hash
        cfg.crypto_backend = 'rsa_pkcs1_5'
        cfg.should_use_hash = lambda _: True
        self.run_scenario(suffix='RsaPkcs15', use_cache=cfg.use_circuit_cache_during_testing_with_encryption)
        cfg.crypto_backend = old
        cfg.should_use_hash = old_sh


# @parameterized_class(('name', 'scenario'), enc_scenarios)
# class TestOffchainRsaOaepEnc(TestOffchainBase):
#     def test_offchain_simulation_rsa_oaep(self):
#         old = cfg.crypto_backend
#         old_sh = cfg.should_use_hash
#         cfg.crypto_backend = 'rsa_oaep'
#         cfg.should_use_hash = lambda _: True
#         self.run_scenario(suffix='RsaOaep', use_cache=cfg.use_circuit_cache_during_testing_with_encryption)
#         cfg.crypto_backend = old
#         cfg.should_use_hash = old_sh
