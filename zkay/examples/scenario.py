import os
from typing import Any, Optional, List, Union, Dict, Type
from unittest import TestCase

from zkay.config import cfg
from zkay.transaction.offchain import ContractSimulator
from zkay.transaction.types import AddressValue
from zkay.zkay_ast.ast import TypeName


class TransactionAssertion:
    def check_assertion(self, test: TestCase, user_terminals: Dict[str, Any]):
        pass


class ContractBalanceAssertion(TransactionAssertion):
    def __init__(self, expected_balance) -> None:
        super().__init__()
        self.balance = expected_balance

    def check_assertion(self, test: TestCase, user_terminals: Dict[str, Any]):
        contract_addr = AddressValue(next(iter(user_terminals.values())).address)
        actual_balance = contract_addr.balance
        test.assertEqual(self.balance, actual_balance)


class StateValueAssertion(TransactionAssertion):
    def __init__(self, name: str, *indices, user: str, should_decrypt: bool, plain_type: Optional[TypeName], expected_value) -> None:
        super().__init__()
        self.user = user
        self.name = name
        self.indices = indices
        self.should_decrypt = should_decrypt
        self.plain_type = plain_type

        self.expected = expected_value

    def check_assertion(self, test: TestCase, user_terminals: Dict[str, Any]):
        # Replace user names by the corresponding address
        indices = [user_terminals[user].api.user_address if user in user_terminals else user for user in self.indices]

        user = next(iter(user_terminals.values())) if self.user is None else user_terminals[self.user]
        actual_val = user.api.req_state_var(self.name, *indices, should_decrypt=self.should_decrypt)
        if self.should_decrypt and self.plain_type is not None and self.plain_type.is_signed_numeric:
            actual_val = ContractSimulator.cast(actual_val, self.plain_type.elem_bitwidth, signed=True)
        ind_str = f"[{', '.join([str(i) for i in self.indices])}]" if self.indices else ''
        test.assertEqual(self.expected, actual_val, f"Assertion {self.name}{ind_str} == {self.expected}")


class Transaction:
    def __init__(self, user: str, name: str, *args: Any, amount: Optional[int] = None, expected_exception: Optional[Exception] = None):
        super().__init__()
        self.user = user
        self.name = name
        self.args = args
        self.amount = amount
        self.expected_exception = expected_exception

    def __str__(self):
        return f"{self.name}({', '.join([str(arg) for arg in self.args])}){{amount={self.amount}, user={self.user}}}"


class Scenario:
    def __init__(self, name: str, contract_file_location: str):
        self._name = name
        self.file_location = contract_file_location
        _, self.filename = os.path.split(contract_file_location)
        self._users = None
        self._deployment_transaction = None
        self._transactions_or_assertions = []

    def with_root(self, root: str) -> 'Scenario':
        self.file_location = os.path.join(root, self.file_location)
        return self

    def code(self):
        with open(self.file_location, 'r') as file:
            return file.read().replace('\t', cfg.indentation)

    def name(self):
        return self._name

    def users(self) -> List[str]:
        # Number of users which participate
        return self._users

    def deployment_transaction(self) -> Transaction:
        return self._deployment_transaction

    def transactions_and_assertions(self) -> List[Union[Transaction, TransactionAssertion]]:
        # List of transactions to issue in this order
        return self._transactions_or_assertions


class ScenarioBuilder:
    def __init__(self, name: str, contract_file_location: str) -> None:
        super().__init__()
        self.scenario = Scenario(name, contract_file_location.replace('/', os.path.sep))

    def set_users(self, *users: str):
        self.scenario._users = list(users)
        return self

    def set_deployment_transaction(self, *args, amount=None, owner: str):
        assert self.scenario._deployment_transaction is None
        t = Transaction(owner, '', *args, amount=amount)
        self.scenario._deployment_transaction = t
        return t

    def add_transaction(self, fname: str, args: Optional[List] = None, *, user: str, amount=None, expected_exception=None):
        args = [] if args is None else args
        t = Transaction(user, fname, *args, amount=amount, expected_exception=expected_exception)
        self.scenario._transactions_or_assertions.append(t)
        return t

    def add_state_assertion(self, name: str, *indices, user: str = None, should_decrypt: bool = False, plain_type: Optional[TypeName] = None, expected_value):
        a = StateValueAssertion(name, *indices,user=user, should_decrypt=should_decrypt, plain_type=plain_type, expected_value=expected_value)
        self.scenario._transactions_or_assertions.append(a)
        return self

    def add_balance_assertion(self, expected_balance):
        a = ContractBalanceAssertion(expected_balance)
        self.scenario._transactions_or_assertions.append(a)
        return self

    def build(self) -> Scenario:
        assert self.scenario.users() is not None
        assert self.scenario.deployment_transaction() is not None
        return self.scenario

