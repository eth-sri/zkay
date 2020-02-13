import os
import re
import hashlib
from typing import Optional, List
from zkay.compiler.solidity.fake_solidity_generator import WS_PATTERN, ID_PATTERN


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


def hash_string(data: str) -> bytes:
    digest = hashlib.sha512(data).digest()
    assert len(digest) == 64
    return digest[:32]


def hash_file(filename: str, chunk_size: int = 1 << 27) -> bytes:
    digest = hashlib.sha512()
    with open(filename, 'rb') as f:
        while True:
            # Hash prover key in 128mb chunks
            data = f.read(chunk_size)
            if not data:
                break
            digest.update(data)
    digest = digest.digest()
    assert len(digest) == 64
    return digest[:32]


def without_extension(filename: str) -> str:
    ext_idx = filename.rfind('.')
    ext_idx = len(filename) if ext_idx == -1 else ext_idx
    return filename[:ext_idx]


def get_contract_names(sol_filename: str) -> List[str]:
    with open(sol_filename) as f:
        s = f.read()
        matches = re.finditer(f'contract{WS_PATTERN}*({ID_PATTERN}){WS_PATTERN}*{{', s)
        return [m.group(1) for m in matches]


def prepend_to_lines(text: str, pre: str):
    return pre + text.replace("\n", "\n" + pre)


def lines_of_code(code: str):
    lines = code.split('\n')
    lines = [l for l in lines if not l.startswith('//')]
    return len(lines)
