import inspect
from typing import Dict, Union, Callable, Any, Optional, List

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.types import AddressValue, RandomnessValue, CipherValue, MsgStruct, BlockStruct, TxStruct
from zkay.transaction.runtime import Runtime

uint256_scalar_field = 1 << 256
bn128_scalar_field = bn128_scalar_field
_bn128_comp_scalar_field = 1 << 252


class ContractSimulator:
    def __init__(self, project_dir: str, user_addr: AddressValue):
        self.project_dir = project_dir
        self.conn = Runtime.blockchain()
        self.crypto = Runtime.crypto()
        self.keystore = Runtime.keystore()
        self.prover = Runtime.prover()

        self.current_priv_values: Dict[str, Union[int, bool, RandomnessValue]] = {}
        self.all_priv_values: List[Union[int, bool, RandomnessValue]] = []
        self.current_all_index = None

        self.state_values: Dict[str, Union[int, bool, CipherValue, AddressValue]] = {}
        self.is_external: Optional[bool] = None

        self.contract_handle = None
        self.user_addr = user_addr

        self.current_msg: Optional[MsgStruct] = None
        self.current_block: Optional[BlockStruct] = None
        self.current_tx: Optional[TxStruct] = None

    @property
    def address(self):
        return self.contract_handle.address

    @staticmethod
    def comp_overflow_checked(val: int):
        assert val < _bn128_comp_scalar_field, f'Value {val} is too large for comparison'
        return val

    def _call(self, sec_offset, fct, *args) -> Any:
        with CallCtx(self, sec_offset):
            return fct(*args)

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

    @staticmethod
    def my_address() -> AddressValue:
        return Runtime.blockchain().my_address

    @staticmethod
    def create_dummy_accounts(count: int):
        return Runtime.blockchain().create_test_accounts(count)


class FunctionCtx:
    def __init__(self, v: ContractSimulator, trans_sec_size, *, value: int = 0):
        self.v = v
        self.was_external = None
        self.trans_sec_size = trans_sec_size
        self.value = value

    def __enter__(self):
        self.was_external = self.v.is_external
        if self.v.is_external is None:
            self.v.is_external = True
            self.v.state_values.clear()
            self.v.all_priv_values = [0 for _ in range(self.trans_sec_size)]
            self.v.current_all_index = 0
            self.v.current_priv_values.clear()
            self.v.current_msg, self.v.current_block, self.v.current_tx = self.v.conn.get_special_variables(self.v.user_addr, self.value)
        else:
            self.v.is_external = False

    def __exit__(self, t, value, traceback):
        if self.v.is_external:
            self.v.state_values.clear()
            self.v.all_priv_values = None
            self.v.current_all_index = 0
            self.v.current_priv_values.clear()
            self.v.current_msg, self.v.current_block, self.v.current_tx = None, None, None
        self.v.is_external = self.was_external


class CallCtx:
    def __init__(self, v: ContractSimulator, sec_offset):
        self.v = v
        self.sec_offset = sec_offset

        self.old_priv_values = None
        self.old_all_idx = None

    def __enter__(self):
        self.old_priv_values = self.v.current_priv_values
        self.v.current_priv_values = {}
        self.old_all_idx = self.v.current_all_index
        self.v.current_all_index += self.sec_offset

    def __exit__(self, t, value, traceback):
        self.v.current_priv_values = self.old_priv_values
        self.v.current_all_index = self.old_all_idx
