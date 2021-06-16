import contextlib
import time

from zkay import my_logging
from zkay.config import zk_print


@contextlib.contextmanager
def time_measure(key, should_print=False, skip=False):
    start = time.time()
    yield
    end = time.time()
    elapsed = end - start

    if not skip:
        if should_print:
            zk_print(f"Took {elapsed} s")
        my_logging.data("time_" + key, elapsed)


class Timer(object):

    def __init__(self, key):
        self.key = key

    def __call__(self, method):
        def timed(*args, **kw):
            with time_measure(self.key):
                result = method(*args, **kw)
                return result

        return timed
