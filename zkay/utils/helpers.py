import os
from typing import Optional


def save_to_file(output_directory: Optional[str], filename: str, code: str):
    if output_directory is not None:
        target = os.path.join(output_directory, filename)
    else:
        target = filename
    with open(target, "w") as f:
        f.write(code)
    return filename


def read_file(filename: str):
    with open(filename, 'r') as f:
        return f.read()


def prepend_to_lines(text: str, pre: str):
    return pre + text.replace("\n", "\n" + pre)


def lines_of_code(code: str):
    lines = code.split('\n')
    lines = [l for l in lines if not l.startswith('//')]
    return len(lines)
