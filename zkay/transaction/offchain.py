import inspect
from contextlib import contextmanager
from enum import Enum
from typing import Dict, Union, Callable, Any, Optional, List, Tuple, Type

from zkay.config import cfg
from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.types import AddressValue, RandomnessValue, CipherValue, MsgStruct, BlockStruct, TxStruct
from zkay.transaction.runtime import Runtime
from zkay.utils.progress_printer import colored_print, TermColor

bn128_scalar_field = bn128_scalar_field
_bn128_comp_scalar_field = 1 << 252


class RequireException(Exception):
    pass


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

    @staticmethod
    def cast(val: Union[int, Enum], nbits: int, *, signed: bool = False, enum: Optional[Type[Enum]] = None):
        # python ints are always signed, is expected to be within range of its type
        if isinstance(val, Enum):
            val = val.value

        trunc_val = val & ((1 << nbits) - 1)
        if signed and trunc_val & (1 << (nbits - 1)):
            trunc_val -= (1 << nbits)

        if enum is not None:
            return enum(trunc_val)
        else:
            return trunc_val

    def _call(self, sec_offset, fct, *args) -> Any:
        with self.call_ctx(sec_offset):
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
            if self.is_external is None and count == 0 and is_encrypted:
                count = cfg.cipher_len

            if count == 0:
                val = val_constructor(self.conn.req_state_var(self.contract_handle, name, *indices))
            else:
                val = val_constructor([self.conn.req_state_var(self.contract_handle, name, *indices, i) for i in range(count)])
            if is_encrypted:
                val = CipherValue(val)

            if self.is_external is not None:
                self.state_values[loc] = val
            elif is_encrypted:
                # Decrypt encrypted values if get state was called standalone
                val = self.crypto.dec(val, self.keystore.sk(self.user_addr))[0]
            return val

    @staticmethod
    def my_address() -> AddressValue:
        return Runtime.blockchain().my_address

    @staticmethod
    def init_key_pair(address: str):
        account = AddressValue(address)
        key_pair = Runtime.crypto().generate_or_load_key_pair(account)
        Runtime.keystore().add_keypair(account, key_pair)

    @staticmethod
    def create_dummy_accounts(count: int) -> Union[str, Tuple]:
        accounts = Runtime.blockchain().create_test_accounts(count)
        for account in accounts:
            ContractSimulator.init_key_pair(account)
        if len(accounts) == 1:
            return accounts[0]
        else:
            return accounts

    @contextmanager
    def call_ctx(self, sec_offset):
        old_priv_values, old_all_idx = self.current_priv_values, self.current_all_index
        self.current_priv_values = {}
        self.current_all_index += sec_offset
        yield
        self.current_priv_values, self.current_all_index = old_priv_values, old_all_idx


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

    def __exit__(self, exec_type, exec_value, traceback):
        if self.v.is_external:
            self.v.state_values.clear()
            self.v.all_priv_values = None
            self.v.current_all_index = 0
            self.v.current_priv_values.clear()
            self.v.current_msg, self.v.current_block, self.v.current_tx = None, None, None

        self.v.is_external = self.was_external

        if exec_type == RequireException:
            if self.v.is_external is None and not cfg.is_unit_test:
                with colored_print(TermColor.FAIL):
                    print(f'ERROR: {exec_value}')
                return True
