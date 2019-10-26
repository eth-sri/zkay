import contextlib
from typing import List

full_log_context: List = []


@contextlib.contextmanager
def log_context(key: str, value):
    found = find_key(key) is not None
    if not found:
        add_log_context(key, value)
    yield
    if not found:
        remove_log_context(key)


def add_log_context(key: str, value):
    assert key is not None
    assert value is not None

    full_log_context.append([key, value])


def find_key(key):
    for i, item in enumerate(full_log_context):
        if key == item[0]:
            return i
    return None


def remove_log_context(key):
    i = find_key(key)
    if i is None:
        raise ValueError(f'Key {key} not found')
    del full_log_context[i]
