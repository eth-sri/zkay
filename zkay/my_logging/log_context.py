import contextlib
from typing import List

full_log_context: List = []


@contextlib.contextmanager
def log_context(key: str):
    full_log_context.append(key)
    yield
    full_log_context.pop()
