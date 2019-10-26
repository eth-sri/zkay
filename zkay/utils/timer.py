import contextlib
import time

from zkay import my_logging


@contextlib.contextmanager
def time_measure(key):
    start = time.time()
    yield
    end = time.time()
    elapsed = end - start

    my_logging.data(key, elapsed)


class Timer(object):

    def __init__(self, key):
        self.key = key

    def __call__(self, method):
        def timed(*args, **kw):
            with time_measure(self.key):
                result = method(*args, **kw)
                return result

        return timed
