import contextlib


@contextlib.contextmanager
def print_step(name):
	print(f'{name}... ', end='', flush=True)
	yield
	print('done')
