from typing import List

from parameterized import parameterized_class

from zkay.examples.examples import all_examples, Example
from zkay.examples.scenario import TransactionAssertion
from zkay.examples.scenarios import Scenario
from zkay.tests.zkay_unit_test import ZkayTestCase


class TestExamples(ZkayTestCase):
    name: str = None
    example: Example = None


class TestScenario(ZkayTestCase):
    name: str = None
    scenario: Scenario = None

    def check_transaction_assertions(self, users, assertions: List[TransactionAssertion]):
        for assertion in assertions:
            assertion.check_assertion(self, users)


@parameterized_class(('name', 'example'), all_examples)
class TestExamplesFunctions(TestExamples):

    def test_file_location(self):
        self.assertIsNotNone(self.example.file_location)

    def test_code(self):
        self.assertIsNotNone(self.example.code())

    def test_stream(self):
        self.assertIsNotNone(self.example.stream())

    def test_name(self):
        self.assertIsNotNone(self.example.name())
