import os
import sys
from contextlib import contextmanager

# Based on https://stackoverflow.com/a/17954769
from zkay.config import cfg


@contextmanager
def output_suppressed(key: str):
    fd = sys.stdout.fileno()

    def _redirect_stdout(to):
        sys.stdout.close()
        os.dup2(to.fileno(), fd)
        sys.stdout = os.fdopen(fd, 'w')

    if key in cfg.debug_output_whitelist:
        yield
    else:
        with os.fdopen(os.dup(fd), 'w') as old_stdout:
            with open(os.devnull, 'w') as file:
                _redirect_stdout(to=file)
            try:
                yield
            finally:
                _redirect_stdout(to=old_stdout)
