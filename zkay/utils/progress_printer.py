import contextlib
from enum import Enum

from zkay.config import zk_print


@contextlib.contextmanager
def print_step(name):
    zk_print(f'{name}... ', end='', flush=True)
    yield
    zk_print('done')


class TermColor(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@contextlib.contextmanager
def colored_print(color: TermColor):
    print(color.value, end='')
    yield
    print(TermColor.ENDC.value, end='')
