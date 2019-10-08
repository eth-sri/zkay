import json
import time
import unittest

import my_logging
from utils.helpers import read_file
from utils.timer import Timer, time_measure


@Timer('mykey')
def sleep(n):
    time.sleep(n)


base_log_file = my_logging.get_log_file(label='TestTimer')


class TestTimer(unittest.TestCase):

    def test_timer_decorator(self):
        log_file = base_log_file + '_decorator'
        my_logging.prepare_logger(log_file)
        sleep(0.5)
        my_logging.shutdown()

        content = read_file(log_file + '_data.log')

        d = json.loads(content)
        self.assertAlmostEqual(0.5, d['value'], 1)

    def test_timer_context_manager(self):
        log_file = base_log_file + '_context_manager'
        my_logging.prepare_logger(log_file)
        my_logging.shutdown()

        with time_measure('mykey2'):
            time.sleep(0.5)

        content = read_file(log_file + '_data.log')
        d = json.loads(content)
        self.assertAlmostEqual(0.5, d['value'], 1)
