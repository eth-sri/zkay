from __future__ import annotations

import inspect
from contextlib import contextmanager
from enum import Enum, IntEnum
from typing import Dict, Union, Callable, Any, Optional, List, Tuple, Type, ContextManager

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.compiler.privacy.manifest import Manifest
from zkay.config import cfg
from zkay.transaction.int_casts import __convert as int_cast
from zkay.transaction.interface import parse_manifest, BlockChainError
from zkay.transaction.runtime import Runtime
from zkay.transaction.types import AddressValue, RandomnessValue, CipherValue, MsgStruct, BlockStruct, TxStruct, Value, PrivateKeyValue, \
    PublicKeyValue
from zkay.utils.progress_printer import colored_print, TermColor

bn128_scalar_field = bn128_scalar_field
_bn128_comp_scalar_field = 1 << 252


class RequireException(Exception):
    pass


class StateDict:
    """Dictionary which wraps access to state variables"""

    def __init__(self, api) -> None:
        self.api = api
        self.__state: Dict[str, Any] = {}
        self.__constructors: Dict[str, Callable] = {}

    def clear(self):
        self.__state.clear()

    def decl(self, name, constructor: Callable = lambda x: x):
        """Define the wrapper constructor for a state variable."""
        assert name not in self.__constructors
        self.__constructors[name] = constructor

    def __getitem__(self, key: Union[str, Tuple]):
        """
        Return value of the state variable (or index of state variable) key

        :param key: Either a string with the state variable name (primitive variables) or a Tuple with the name and all index key values
        :raise KeyError: if location does not exist on the chain
        :return: The requested value
        """
        if not isinstance(key, Tuple):
            key = (key, )
        var, indices = key[0], key[1:]
        loc = var + ''.join(f'[{k}]' for k in key[1:])

        # Retrieve from state scope
        if loc in self.__state:
            return self.__state[loc]
        else:
            constr = self.__constructors[var]
            try:
                val = constr(self.api.req_state_var(var, *indices, count=(cfg.cipher_len if constr == CipherValue else 0)))
            except BlockChainError:
                raise KeyError(key)
            self.__state[loc] = val
            return val

    def __setitem__(self, key, value):
        """
        Assign value to state variable (or to index of state variable)

        :param key: Either a string with the state variable name (primitive variables) or a Tuple with the name and all index key values
        :param value: Correctly wrapped value which should be assigned to the specified state location
        """

        if not isinstance(key, Tuple):
            key = (key, )
        var = key[0]
        loc = var + ''.join(f'[{k}]' for k in key[1:])

        # Write to state
        self.__state[loc] = value


class LocalsDict:
    """
    Dictionary which supports multiple scopes with name shadowing.

    This is needed since python does not natively support c-style nested local scopes.
    """
    def __init__(self) -> None:
        self._scopes: List[dict] = [{}]

    def push_scope(self):
        """Introduce a new scope."""
        self._scopes.append({})

    def pop_scope(self):
        """End the current scope."""
        self._scopes.pop()

    def decl(self, name, val):
        """Introduce a new local variable with the given name and value into the current scope."""
        if name in self._scopes[-1]:
            raise ValueError('Variable declared twice in same scope')
        self._scopes[-1][name] = val

    def __getitem__(self, key):
        """
        Return the value of the local variable which is referenced by the identifier key in the current scope.

        If there are multiple variables with the name key in different scopes,
        the variable with the lowest declaration scope is used.
        """
        for scope in reversed(self._scopes):
            if key in scope:
                return scope[key]
        raise ValueError('Variable not found')

    def __setitem__(self, key, value):
        """
        Assign value to the local variable which is referenced by the identifier key in the current scope.

        If there are multiple variables with the name key in different scopes, the variable with the lowest declaration scope is used.
        """
        for scope in reversed(self._scopes):
            if key in scope:
                scope[key] = value
                return
        raise ValueError('Variable not found')


class ContractSimulator:
    def __init__(self, project_dir: str, user_addr: AddressValue, contract_name: str):
        """
        Create new contract simulator instance.

        :param project_dir: Directory where the zkay contract, the manifest and the prover/verification key files are located
        :param user_addr: From address for all transactions which are issued by this ContractSimulator
        """
        self.api = ApiWrapper(project_dir, contract_name, user_addr)

        # Transaction instance values (reset between transactions)

        self.locals: Optional[LocalsDict] = None
        """Hierarchical dictionary (scopes are managed internally) which holds the currently accessible local variables"""

        self.state: StateDict = StateDict(self.api)
        """
        Dict which stores stores state variable values. Empty at the beginning of a transaction.
        State variable read: 1. if not in dict -> request from chain and insert into dict, 2. return dict value
        State variable write: store in dict
        """

    @property
    def address(self):
        return self.api.address

    @contextmanager
    def scope(self) -> ContextManager:
        """Return context manager which manages the lifetime of a local scope."""
        self.locals.push_scope()
        yield
        self.locals.pop_scope()

    @staticmethod
    def cast(val: Union[int, Enum, AddressValue], nbits: Optional[int], *, signed: bool = False, constr: Optional[Type] = None):
        """
        Convert primitive type value to a different primitive type

        :param val: value to convert (either int, enum or address)
        :param nbits: bitcount of the target type, if None -> target type is a field value / private uint256 (overflow at FIELD_PRIME)
        :param signed: signedness of the target type
        :param constr: value constructor for the target type (for enums and address only)
        :return: converted value
        """
        trunc_val = int_cast(val, nbits, signed)
        if constr is not None:
            return constr(trunc_val)
        else:
            return trunc_val

    @staticmethod
    def help(global_fcts, members, contract_name):
        """Display help for contract functions."""
        signatures = [(fname, str(inspect.signature(sig))) for fname, sig in global_fcts]
        print("Global functions:")
        print('\n'.join([f'{fname}({sig[1:]}' for fname, sig in signatures
                         if not fname.startswith('_') and fname != 'help']))
        print()
        print(f'Members for {contract_name} contract instances (either deploy or connect to create one):')
        signatures = [(fname, str(inspect.signature(sig))) for fname, sig in members]
        print('\n'.join([f'{fname}({sig[5:] if not sig[5:].startswith(",") else sig[7:]}'
                         for fname, sig in signatures
                         if sig.startswith('(self') and not fname.endswith('_check_proof') and not fname.startswith('_')]))

    @staticmethod
    def default_address() -> AddressValue:
        """Return default wallet address (if supported by backend, otherwise empty address is returned)."""
        return Runtime.blockchain().default_address

    @staticmethod
    def initialize_keys_for(address: Union[bytes, str]):
        """Generate/Load keys for the given address."""
        account = AddressValue(address)
        Runtime.crypto().generate_or_load_key_pair(account)

    @staticmethod
    def use_config_from_manifest(project_dir: str):
        """Override zkay configuration with values from the manifest file in project_dir."""

        manifest = parse_manifest(project_dir)

        # Check if zkay version matches
        if manifest[Manifest.zkay_version] != cfg.zkay_version:
            with colored_print(TermColor.WARNING):
                print(
                    f'Zkay version in manifest ({manifest[Manifest.zkay_version]}) does not match current zkay version ({cfg.zkay_version})\n'
                    f'Compilation or integrity check with deployed bytecode might fail due to version differences')

        cfg.override_solc(manifest[Manifest.solc_version])
        cfg.import_compiler_settings(manifest[Manifest.zkay_options])
        Runtime.reset()

    @staticmethod
    def create_dummy_accounts(count: int) -> Union[str, Tuple]:
        """
        Create count pre-funded dummy accounts (if supported by backend)

        :param count: # of accounts to create
        :return: if count == 1 -> returns a address, otherwise returns a tuple of count addresses
        """
        accounts = Runtime.blockchain().create_test_accounts(count)
        for account in accounts:
            ContractSimulator.initialize_keys_for(account)
        if len(accounts) == 1:
            return accounts[0]
        else:
            return accounts

    @contextmanager
    def function_ctx(self, trans_sec_size=-1, *, wei_amount: int = 0):
        with self.api.api_function_ctx(trans_sec_size, wei_amount) as is_external:
            if is_external:
                assert self.locals is None
                self.state.clear()

            prev_locals = self.locals
            self.locals = LocalsDict()

            try:
                yield is_external
            except RequireException as e:
                if is_external and not cfg.is_unit_test:
                    with colored_print(TermColor.FAIL):
                        print(f'ERROR: {e}')
                else:
                    raise e
            finally:
                self.locals = prev_locals
                if is_external:
                    self.state.clear()


class ApiWrapper:
    def __init__(self, project_dir, contract_name, user_addr) -> None:
        super().__init__()
        self.__conn = Runtime.blockchain()
        self.__keystore = Runtime.keystore()
        self.__crypto = Runtime.crypto()
        self.__prover = Runtime.prover()

        self.__project_dir = project_dir
        self.__contract_name = contract_name

        self.__contract_handle = None
        """Handle which refers to the deployed contract, this is passed to the blockchain interface when e.g. issuing transactions."""

        self.__user_addr = user_addr
        """From address for all transactions which are issued by this ContractSimulator"""

        self.__current_msg: Optional[MsgStruct] = None
        self.__current_block: Optional[BlockStruct] = None
        self.__current_tx: Optional[TxStruct] = None
        """
        Builtin variable (msg, block, tx) values for the current transaction
        """

        self.current_priv_values: Dict[str, Union[int, bool, RandomnessValue]] = {}
        """Dictionary which stores the private circuit values (secret inputs) for the current function (no transitivity)"""

        self.all_priv_values: Optional[List[Union[int, bool, RandomnessValue]]] = None
        """List which stores all secret circuit inputs for the current transaction in correct order (order of use)"""

        self.current_all_index: Optional[int] = None
        """
        Index which designates where in all_priv_values the secret circuit inputs of the current function should be inserted.
        This is basically private analogue of the start_index parameters which are passed to functions which require verification
        to designate where in the public IO arrays the functions should store/retrieve public circuit inputs/outputs.
        """

        self.is_external: Optional[bool] = None
        """
        True whenever simulation is inside a function which was directly (without transitivity) called by the user.
        This is mostly used for some checks (e.g. to prevent the user from calling internal functions), or to change
        function behavior depending on whether a call is external or not (e.g. encrypting parameters or not)
        """

    @property
    def address(self):
        return self.__contract_handle.address

    @property
    def user_address(self):
        return self.__user_addr

    @property
    def keystore(self):
        return self.__keystore

    def get_my_sk(self) -> PrivateKeyValue:
        return self.__keystore.sk(self.user_address)

    def get_my_pk(self) -> PublicKeyValue:
        return self.__keystore.pk(self.user_address)

    def call_fct(self, sec_offset, fct, *args) -> Any:
        with self.__call_ctx(sec_offset):
            return fct(*args)

    @staticmethod
    def range_checked(val: int):
        """
        Check whether a comparison with value 'val' can be evaluated correctly in the circuit.

        :param val: the value to check
        :raises ValueError:
        """
        if val >= _bn128_comp_scalar_field:
            raise ValueError(f'Value {val} is too large for comparison, circuit would produce wrong results.')
        return val

    def deploy(self, actual_args: List, should_encrypt: List[bool], wei_amount: Optional[int] = None):
        self.__contract_handle = self.__conn.deploy(self.__project_dir, self.__user_addr, self.__contract_name,
                                                    actual_args, should_encrypt, wei_amount=wei_amount)

    def connect(self, address: AddressValue):
        self.__contract_handle = self.__conn.connect(self.__project_dir, self.__contract_name, address)

    def transact(self, fname: str, args: List, should_encrypt: List[bool], wei_amount: Optional[int] = None) -> Any:
        return self.__conn.transact(self.__contract_handle, self.__user_addr, fname, args, should_encrypt, wei_amount=wei_amount)

    def call(self, fname: str, args: List, ret_val_constructors: List[Optional[Callable]]):
        retvals = self.__conn.call(self.__contract_handle, fname, args)
        assert len(retvals) == len(ret_val_constructors)
        wrapped_retvals = []
        for retval, retval_constr in zip(retvals, ret_val_constructors):
            wrapped_retvals.append(retval if retval_constr is None else retval_constr(retval))
        return wrapped_retvals

    def get_special_variables(self) -> Tuple[MsgStruct, BlockStruct, TxStruct]:
        assert self.__current_msg is not None and self.__current_block is not None and self.__current_tx is not None
        return self.__current_msg, self.__current_block, self.__current_tx

    def update_special_variables(self, wei_amount: int):
        self.__current_msg, self.__current_block, self.__current_tx = self.__conn.get_special_variables(self.__user_addr, wei_amount)

    def clear_special_variables(self):
        self.__current_msg, self.__current_block, self.__current_tx = None, None, None

    def req_state_var(self, name: str, *indices, count=0, should_decrypt=False):
        if should_decrypt:
            count = cfg.cipher_len

        if count == 0:
            val = self.__conn.req_state_var(self.__contract_handle, name, *indices)
        else:
            val = [self.__conn.req_state_var(self.__contract_handle, name, *indices, i) for i in range(count)]

        if should_decrypt:
            val = self.__crypto.dec(CipherValue(val), self.__user_addr)
            if not cfg.is_symmetric_cipher():
                val = val[0]
        return val

    def enc(self, plain: Union[int, AddressValue], target_addr: Optional[AddressValue] = None) -> Union[CipherValue, Tuple[CipherValue, RandomnessValue]]:
        target_addr = self.__user_addr if target_addr is None else target_addr
        return self.__crypto.enc(plain, self.__user_addr, target_addr)

    def dec(self, cipher: CipherValue) -> Union[int, Tuple[int, RandomnessValue]]:
        return self.__crypto.dec(cipher, self.__user_addr)

    @staticmethod
    def __serialize_val(val: Any, bitwidth: int):
        if isinstance(val, AddressValue):
            val = int.from_bytes(val.val, byteorder='big')
        elif isinstance(val, IntEnum):
            val = val.value
        elif isinstance(val, bool):
            val = int(val)
        elif isinstance(val, int):
            if val < 0:
                val = ContractSimulator.cast(val, bitwidth, signed=False)
            elif bitwidth == 256:
                val %= bn128_scalar_field
        return val

    @staticmethod
    def __serialize_circuit_array(data: dict, target_array: List, target_out_start_idx: int, elem_bitwidths: List[int]):
        idx = target_out_start_idx
        for (name, val), bitwidth in zip(data.items(), elem_bitwidths):
            if isinstance(val, (list, Value)) and not isinstance(val, AddressValue):
                target_array[idx:idx + len(val)] = val[:cfg.cipher_payload_len] if isinstance(val, CipherValue) else val[:]
                idx += len(val)
            else:
                target_array[idx] = ApiWrapper.__serialize_val(val, bitwidth)
                idx += 1

    def serialize_circuit_outputs(self, zk_data: dict, out_elem_bitwidths: List[int]) -> List[int]:
        out_vals = {name: val for name, val in zk_data.items() if name.startswith(cfg.zk_out_name)} # TODO don't depend on out var names for correctness
        count = sum([len(val) if isinstance(val, (Tuple, list)) else 1 for val in out_vals.values()])
        zk_out = [None for _ in range(count)]
        self.__serialize_circuit_array(out_vals, zk_out, 0, out_elem_bitwidths)
        return zk_out

    def serialize_private_inputs(self, zk_priv: dict, priv_elem_bitwidths: List[int]):
        self.__serialize_circuit_array(zk_priv, self.all_priv_values, self.current_all_index, priv_elem_bitwidths)

    def gen_proof(self, fname: str, in_vals: List, out_vals: List[Union[int, CipherValue]]) -> List[int]:
        return self.__prover.generate_proof(self.__project_dir, self.__contract_name, fname, self.all_priv_values, in_vals, out_vals)

    @contextmanager
    def __call_ctx(self, sec_offset) -> ContextManager:
        """Return context manager which sets the correct current_all_index for the given sec_offset during its lifetime."""
        old_priv_values, old_all_idx = self.current_priv_values, self.current_all_index
        self.current_priv_values = {}
        self.current_all_index += sec_offset
        yield
        self.current_priv_values, self.current_all_index = old_priv_values, old_all_idx

    @contextmanager
    def api_function_ctx(self, trans_sec_size, wei_amount) -> ContextManager:
        was_external = self.is_external
        if was_external is None:
            assert self.all_priv_values is None
            self.is_external = True
            self.all_priv_values = [0 for _ in range(trans_sec_size)]
            self.current_all_index = 0
            self.current_priv_values.clear()
            self.update_special_variables(wei_amount)
        else:
            self.is_external = False

        try:
            yield self.is_external
        finally:
            if self.is_external:
                assert was_external is None
                self.all_priv_values = None
                self.current_all_index = 0
                self.current_priv_values.clear()
                self.clear_special_variables()

            self.is_external = was_external
