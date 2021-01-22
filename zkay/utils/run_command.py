import os
import subprocess

from zkay.config import cfg
from typing import List, Optional, Tuple


def run_command(cmd: List[str], cwd=None, allow_verbose: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Run arbitrary command.

    :param cmd: the command to run (list of command and arguments)
    :param cwd: if specified, use this path as working directory (otherwise current working directory is used)
    :param allow_verbose: if true, redirect command output to stdout (WARNING, causes return values to be None)
    :return: command output and error output (if not (allow_verbose and cfg.verbosity))
    """

    if cwd is not None:
        cwd = os.path.abspath(cwd)

    if allow_verbose and cfg.verbosity >= 2 and not cfg.is_unit_test:
        process = subprocess.Popen(cmd, cwd=cwd)
        output, error = process.communicate() # will be None
    else:
        # run
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)

        # collect output
        output, error = process.communicate()

        # decode output
        output = output.decode('utf-8').rstrip()
        error = error.decode('utf-8').rstrip()

    # check for error
    if process.returncode != 0:
        cmd = get_command(cmd)
        msg = f"Non-zero exit status {process.returncode} for command:\n{cwd}: $ {cmd}\n\n{output}\n{error}"
        raise subprocess.SubprocessError(msg)
    elif cfg.verbosity >= 2:
        print(f'Ran command {get_command(cmd)}:\n\n{output}\n{error}')

    return output, error


def get_command(cmd: List[str]):
    def format_part(p: str):
        if ' ' in p:
            return f'"{p}"'
        else:
            return p

    str_command = " ".join(format_part(p) for p in cmd)
    return str_command
