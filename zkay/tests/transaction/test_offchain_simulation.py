import importlib
import os
import shutil
import sys
import unittest
from contextlib import nullcontext, contextmanager
from typing import Optional

from parameterized import parameterized_class

from zkay.zkay_frontend import compile_zkay
from zkay.config import cfg
from zkay.examples.scenario import TransactionAssertion, Transaction
from zkay.examples.example_scenarios import all_scenarios, enc_scenarios, get_scenario
from zkay.tests.utils.test_examples import TestScenarios
from zkay.transaction.runtime import Runtime

# get relevant paths

output_dir = os.path.join(cfg.log_dir, 'transaction_tests', 'output')
os.makedirs(output_dir, exist_ok=True)
with open(os.path.join(output_dir, '__init__.py'), mode='w'):
    pass


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
        cg, code = compile_zkay(c, d)
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
        deployment_args = [user_addresses[user] if user in user_addresses else user for user in deployment_transaction.args]
        owner = deployment_transaction.user
        contract_address = None
        for user, address in user_addresses.items():
            if user == owner:
                if deployment_transaction.amount is None:
                    contract = oc.deploy(*deployment_args, user=address)
                else:
                    contract = oc.deploy(*deployment_args, user=address, wei_amount=deployment_transaction.amount)
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
                print(f'Transaction: {trans_or_assert}')
                assert isinstance(trans_or_assert, Transaction)
                exception = trans_or_assert.expected_exception
                with nullcontext() if exception is None else self.assertRaises(exception):
                    # Execute transaction
                    transact = getattr(users[trans_or_assert.user], trans_or_assert.name)
                    args = [users[user].api.user_address.val if user in users else user for user in trans_or_assert.args]
                    if trans_or_assert.amount is None:
                        receipt = transact(*args)
                    else:
                        receipt = transact(*args, wei_amount=trans_or_assert.amount)
                    self.assertIsNotNone(receipt)

        if not use_cache:
            shutil.rmtree(d)


@contextmanager
def _mock_config(crypto: str, crypto_addhom: Optional[str], hash_opt, blockchain: str = 'w3-eth-tester'):
    old_c_nh, old_c_add = cfg.main_crypto_backend, cfg.addhom_crypto_backend
    old_h, old_b = cfg.should_use_hash, cfg.blockchain_backend
    cfg.main_crypto_backend = crypto
    cfg.addhom_crypto_backend = crypto_addhom
    cfg.should_use_hash = (lambda _: hash_opt) if isinstance(hash_opt, bool) else hash_opt
    cfg.blockchain_backend = blockchain
    yield
    cfg.main_crypto_backend, cfg.addhom_crypto_backend = old_c_nh, old_c_add
    cfg.should_use_hash, cfg.blockchain_backend = old_h, old_b


#@parameterized_class(('name', 'scenario'), get_scenario('.py'))
@parameterized_class(('name', 'scenario'), all_scenarios)
class TestOffchainDummyEnc(TestOffchainBase):
    @unittest.skipIf(False, "No reason")
    def test_offchain_simulation_dummy(self):
        with _mock_config('dummy', 'dummy-hom', False):
            self.run_scenario()


@parameterized_class(('name', 'scenario'), get_scenario('enctest.py'))
class TestOffchainWithHashing(TestOffchainBase):
    @unittest.skipIf(False, "No reason")
    def test_offchain_simulation_dummy_with_hashing(self):
        with _mock_config('dummy', 'dummy-hom', True):
            self.run_scenario(suffix='WithHashing')


@parameterized_class(('name', 'scenario'), enc_scenarios)
class TestOffchainEcdhChaskeyEnc(TestOffchainBase):
    @unittest.skipIf(False or 'ZKAY_SKIP_REAL_ENC_TESTS' in os.environ and os.environ['ZKAY_SKIP_REAL_ENC_TESTS'] == '1', 'real encryption tests disabled')
    def test_offchain_simulation_ecdh_chaskey(self):
        with _mock_config('ecdh-chaskey', None, True):
            self.run_scenario(suffix='EcdhChaskey', use_cache=cfg.use_circuit_cache_during_testing_with_encryption)


@parameterized_class(('name', 'scenario'), enc_scenarios)
class TestOffchainEcdhAesEnc(TestOffchainBase):
    @unittest.skipIf(False or 'ZKAY_SKIP_REAL_ENC_TESTS' in os.environ and os.environ['ZKAY_SKIP_REAL_ENC_TESTS'] == '1', 'real encryption tests disabled')
    def test_offchain_simulation_ecdh_aes(self):
        with _mock_config('ecdh-aes', None, True):
            self.run_scenario(suffix='EcdhAes', use_cache=cfg.use_circuit_cache_during_testing_with_encryption)


@parameterized_class(('name', 'scenario'), enc_scenarios)
class TestOffchainRsaPkcs15Enc(TestOffchainBase):
    @unittest.skipIf(False or 'ZKAY_SKIP_REAL_ENC_TESTS' in os.environ and os.environ['ZKAY_SKIP_REAL_ENC_TESTS'] == '1', 'real encryption tests disabled')
    def test_offchain_simulation_rsa_pkcs_15(self):
        with _mock_config('rsa-pkcs1.5', None, True):
            self.run_scenario(suffix='RsaPkcs15', use_cache=cfg.use_circuit_cache_during_testing_with_encryption)


@parameterized_class(('name', 'scenario'), enc_scenarios)
class TestOffchainRsaOaepEnc(TestOffchainBase):
    @unittest.skipIf(True or 'ZKAY_SKIP_REAL_ENC_TESTS' in os.environ and os.environ['ZKAY_SKIP_REAL_ENC_TESTS'] == '1', 'real encryption tests disabled')
    def test_offchain_simulation_rsa_oaep(self):
        with _mock_config('rsa-oaep', None, True):
            self.run_scenario(suffix='RsaOaep', use_cache=cfg.use_circuit_cache_during_testing_with_encryption)


@parameterized_class(('name', 'scenario'), enc_scenarios)
class TestOffchainPaillierEnc(TestOffchainBase):
    @unittest.skipIf(False or 'ZKAY_SKIP_REAL_ENC_TESTS' in os.environ and os.environ['ZKAY_SKIP_REAL_ENC_TESTS'] == '1', 'real encryption tests disabled')
    def test_offchain_simulation_paillier(self):
        with _mock_config('paillier', None, True):
            self.run_scenario(suffix='Paillier', use_cache=cfg.use_circuit_cache_during_testing_with_encryption)


@parameterized_class(('name', 'scenario'), all_scenarios)
class TestOffchainElgamal(TestOffchainBase):
    @unittest.skipIf(
        False or 'ZKAY_SKIP_REAL_ENC_TESTS' in os.environ and os.environ['ZKAY_SKIP_REAL_ENC_TESTS'] == '1', 'real encryption tests disabled')
    def test_offchain_simulation_elgamal(self):
        with _mock_config('elgamal', 'elgamal', False):
            self.run_scenario()
