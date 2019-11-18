import inspect
from typing import Dict, Union, Callable, Any

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.interface import AddressValue, RandomnessValue, CipherValue
from zkay.transaction.runtime import Runtime

uint256_scalar_field = 1 << 256
bn128_scalar_field = bn128_scalar_field
_bn128_comp_scalar_field = 1 << 252


class ContractSimulator:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.conn = Runtime.blockchain()
        self.crypto = Runtime.crypto()
        self.keystore = Runtime.keystore()
        self.prover = Runtime.prover()

        self.priv_values: Dict[str, Union[int, bool, RandomnessValue]] = {}
        self.state_values: Dict[str, Union[int, bool, CipherValue, AddressValue]] = {}
        self.is_external: bool = True

        self.contract_handle = None

    @property
    def address(self):
        return self.contract_handle.address

    @staticmethod
    def comp_overflow_checked(val: int):
        assert val < _bn128_comp_scalar_field, f'Value {val} is too large for comparison'
        return val

    @staticmethod
    def help(members):
        signatures = [(fname, str(inspect.signature(sig))) for fname, sig in members]
        print('\n'.join([f'{fname}({sig[5:] if not sig[5:].startswith(",") else sig[7:]}'
                         for fname, sig in signatures
                         if sig.startswith('(self') and not fname.endswith('_check_proof') and not fname.startswith('_')]))

    def get_state(self, name: str, *indices, count=0, is_encrypted=False, val_constructor: Callable[[Any], Any] = lambda x: x):
        idxvals = ''.join([f'[{idx}]' for idx in indices])
        loc = f'{name}{idxvals}'
        if loc in self.state_values:
            return self.state_values[loc]
        else:
            if count == 0:
                val = val_constructor(self.conn.req_state_var(self.contract_handle, name, *indices))
            else:
                val = val_constructor([self.conn.req_state_var(self.contract_handle, name, *indices, i) for i in range(count)])
            if is_encrypted:
                val = CipherValue(val)
            self.state_values[loc] = val
            return val


class CleanState:
    def __init__(self, v: ContractSimulator):
        self.v = v
        self.was_external = None

    def __enter__(self):
        if self.v.is_external:
            self.v.state_values.clear()
            self.v.priv_values.clear()
        self.was_external = self.v.is_external
        self.v.is_external = False

    def __exit__(self, t, value, traceback):
        self.v.is_external = self.was_external
        if self.v.is_external:
            self.v.state_values.clear()
            self.v.priv_values.clear()
