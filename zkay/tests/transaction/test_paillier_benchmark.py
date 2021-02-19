import os
import subprocess
import time
import unittest
from contextlib import contextmanager
from typing import List, Optional, Tuple

from zkay.config import cfg
from zkay.jsnark_interface import libsnark_interface
from zkay.examples.example_scenarios import get_scenario
from zkay.tests.transaction.test_offchain_simulation import TestOffchainBase
from zkay.utils import run_command
from zkay.utils.run_command import get_command

# Running this benchmark prints a CSV (or TSV if you set SEP = '\t') to stdout with the following columns:
#   key_bits: Length of Paillier public key 'n'
#   keygen_*:    '*' required to run libsnark key generation on a zkay file with a single Paillier encryption
#   prove_*:     '*' required to run libsnark to create a proof for said zkay file and the CRS created by keygen
# where * is:
#   realtime_s:  Wall clock time required, in seconds
#   utime_s:     User-mode time in seconds. Likely greater than realtime_s due to use of multiple threads
#   stime_s:     Kernel-mode time in seconds
#   maxrss_kb:   Maximum resident set size during execution of program. Used as a proxy for total memory usage.

STEP_BITS = 2        # Include 2^(STEP_BITS - 1) - 1 values between powers-of-2 in benchmark. 1: Powers-of-2 only
MIN_KEY_BITS = 384   # All bits except for the first STEP_BITS bits must be zero. Must be >= 320
MAX_KEY_BITS = 2048  # All bits except for the first STEP_BITS bits must be zero.
NUM_RUNS = 3         # Number of runs per key size
SEP = ','            # Value separator in output. Some people prefer TSV over CSV

orig_run_command = run_command.run_command


# Unix-only hack on top of Popen to use wait4 instead of waitpid, which also returns resource usage
class PopenWithRes(subprocess.Popen):

    def _try_wait(self, wait_flags):
        try:
            (pid, sts, res) = os.wait4(self.pid, wait_flags)
            self._resources = res
        except ChildProcessError:
            pid = self.pid
            sts = 0
        return (pid, sts)

    def get_resources(self):
        return self._resources


def timed_run_command(cmd: List[str], cwd=None, allow_verbose: bool = False) -> Tuple[Optional[str], Optional[str]]:
    old_realtime = round(time.time(), 3)

    if cwd is not None:
        cwd = os.path.abspath(cwd)

    if allow_verbose and cfg.verbosity >= 2 and not cfg.is_unit_test:
        process = PopenWithRes(cmd, cwd=cwd)
        output, error = process.communicate()  # will be None
    else:
        # run
        process = PopenWithRes(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)

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

    child_realtime = round(time.time() - old_realtime, 3)
    child_res = process.get_resources()
    print('', child_realtime, child_res.ru_utime, child_res.ru_stime, child_res.ru_maxrss, sep=SEP, end='', flush=True)

    return output, error


@contextmanager
def _mock_config(crypto: str, crypto_addhom: Optional[str], hash_opt, blockchain: str = 'w3-eth-tester'):
    old_c_nh, old_c_add = cfg.main_crypto_backend, cfg.addhom_crypto_backend
    old_h, old_b = cfg.should_use_hash, cfg.blockchain_backend
    cfg.main_crypto_backend = crypto
    cfg.addhom_crypto_backend = crypto_addhom
    cfg.should_use_hash = (lambda _: hash_opt) if isinstance(hash_opt, bool) else hash_opt
    cfg.blockchain_backend = blockchain
    libsnark_interface.run_command = timed_run_command
    yield
    cfg.main_crypto_backend, cfg.addhom_crypto_backend = old_c_nh, old_c_add
    cfg.should_use_hash, cfg.blockchain_backend = old_h, old_b
    libsnark_interface.run_command = orig_run_command


def _set_paillier_key_size(key_bits: int):
    from zkay.transaction.crypto.meta import cryptoparams
    cryptoparams['paillier']['key_bits'] = key_bits
    cryptoparams['paillier']['cipher_payload_bytes'] = (2 * key_bits) // 8
    cryptoparams['paillier']['rnd_bytes'] = key_bits // 8


class PaillierBenchmark(TestOffchainBase):
    @unittest.skipIf(False or 'ZKAY_SKIP_REAL_ENC_TESTS' in os.environ and os.environ['ZKAY_SKIP_REAL_ENC_TESTS'] == '1', 'real encryption tests disabled')
    def test_run_benchmark(self):
        self.name, self.scenario = get_scenario('paillier_benchmark.py')[0]
        columns = [
            'key_bits',  # Paillier key size printed in this function
            'keygen_realtime_s', 'keygen_utime_s', 'keygen_stime_s', 'keygen_maxrss_kb',  # First run_command -> keygen
            'prove_realtime_s',  'prove_utime_s',  'prove_stime_s',  'prove_maxrss_kb'    # Second run_command -> prove
        ]
        print(*columns, sep=SEP)

        with _mock_config('paillier', None, True):
            key_bits = MIN_KEY_BITS
            while key_bits <= MAX_KEY_BITS:
                _set_paillier_key_size(key_bits)

                for _ in range(NUM_RUNS):
                    print(key_bits, end='', flush=True)
                    self.run_scenario(suffix='BenchPaillier', use_cache=False)
                    print()  # Finish line with \n

                key_bits += 1 << (key_bits.bit_length() - STEP_BITS)


# I also want to be able to run this directly, without using the unittest framework.
if __name__ == "__main__":
    cfg._is_unit_test = True
    PaillierBenchmark('test_run_benchmark').test_run_benchmark()
