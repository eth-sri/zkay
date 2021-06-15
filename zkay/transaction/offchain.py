from __future__ import annotations

import inspect
from contextlib import contextmanager, nullcontext
from enum import IntEnum
from typing import Dict, Union, Callable, Any, Optional, List, Tuple, ContextManager

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.compiler.privacy.manifest import Manifest
from zkay.config import cfg, zk_print_banner
from zkay.my_logging.log_context import log_context
from zkay.transaction.crypto.params import CryptoParams
from zkay.transaction.int_casts import __convert as int_cast
from zkay.transaction.interface import BlockChainError, ZkayHomomorphicCryptoInterface, ZkayKeystoreInterface
from zkay.transaction.runtime import Runtime
from zkay.transaction.types import AddressValue, RandomnessValue, CipherValue, MsgStruct, BlockStruct, TxStruct, Value, \
    PrivateKeyValue, PublicKeyValue
from zkay.utils.progress_printer import fail_print
from zkay.zkay_ast.homomorphism import Homomorphism

bn128_scalar_field = bn128_scalar_field
_bn128_comp_scalar_field = 1 << 252


class RequireException(Exception):
    pass


class StateDict:
    """Dictionary which wraps access to state variables"""

    def __init__(self, api) -> None:
        self.api = api
        self.__state: Dict[str, Any] = {}
        self.__constructors: Dict[str, (bool, CryptoParams, Callable)] = {}

    def clear(self):
        self.__state.clear()

    def decl(self, name, constructor: Callable = lambda x: x, *,
             cipher: bool = False, crypto_backend: str = cfg.main_crypto_backend):
        """Define the wrapper constructor for a state variable."""
        assert name not in self.__constructors
        self.__constructors[name] = (cipher, CryptoParams(crypto_backend), constructor)

    @property
    def names(self) -> List[str]:
        return list(self.__constructors.keys())

    def get_plain(self, name: str, *indices):
        is_cipher, crypto_params, constr = self.__constructors[name]
        val = self.__get((name, *indices), cache=False)
        if is_cipher:
            ret, _ = self.api.dec(val, constr, crypto_params.crypto_name)
            return ret
        else:
            return val

    def get_raw(self, name: str, *indices):
        return self.__get((name, *indices), cache=False)

    def __getitem__(self, key: Union[str, Tuple]):
        """
        Return value of the state variable (or index of state variable) key

        :param key: Either a string with the state variable name (primitive variables) or a Tuple with the name and all index key values
        :raise KeyError: if location does not exist on the chain
        :return: The requested value
        """
        return self.__get(key, cache=True)

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

    def __get(self, key: Union[str, Tuple], cache: bool):
        if not isinstance(key, Tuple):
            key = (key, )
        var, indices = key[0], key[1:]
        loc = var + ''.join(f'[{k}]' for k in key[1:])

        # Retrieve from state scope
        if cache and loc in self.__state:
            return self.__state[loc]
        else:
            is_cipher, crypto_params, constr = self.__constructors[var]
            try:
                if is_cipher:
                    cipher_len = crypto_params.cipher_len
                    val = CipherValue(self.api._req_state_var(var, *indices, count=cipher_len), params=crypto_params)
                else:
                    val = constr(self.api._req_state_var(var, *indices))
            except BlockChainError:
                raise KeyError(key)
            if cache:
                self.__state[loc] = val
            return val


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
    tidx: Dict[str, int] = {}

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
    def _scope(self) -> ContextManager:
        """Return context manager which manages the lifetime of a local scope."""
        self.locals.push_scope()
        yield
        self.locals.pop_scope()

    @staticmethod
    def help(module, contract, contract_name):
        def pred(obj):
            return inspect.isfunction(obj) and (not hasattr(obj, '_can_be_external') or obj._can_be_external)
        global_fcts = inspect.getmembers(module, inspect.isfunction)
        members = inspect.getmembers(contract, pred)

        """Display help for contract functions."""
        global_fcts = [(name, sig) for name, sig in global_fcts if not name.startswith('int') and not name.startswith('uint')]

        signatures = [(fname, str(inspect.signature(sig))) for fname, sig in global_fcts]
        print("Global functions:")
        print('\n'.join([f'{fname}({sig[1:]}' for fname, sig in signatures
                         if not fname.startswith('_') and fname != 'help' and fname != 'zk__init']))
        print()
        print(f'Members for {contract_name} contract instances (either deploy or connect to create one):')
        signatures = [(fname, str(inspect.signature(sig))) for fname, sig in members]
        print('\n'.join([f'{fname}({sig[5:] if not sig[5:].startswith(",") else sig[7:]}'
                         for fname, sig in signatures
                         if sig.startswith('(self') and not fname.endswith('_check_proof') and not fname.startswith('_')]))

    @staticmethod
    def reduced_help(contract):
        def pred(obj):
            return inspect.isfunction(obj) and (not hasattr(obj, '_can_be_external') or obj._can_be_external) and obj.__name__ != 'constructor'
        members = inspect.getmembers(contract, pred)

        print(f'Externally callable functions:')
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
        for crypto_params in cfg.all_crypto_params():
            if not Runtime.keystore(crypto_params).has_initialized_keys_for(AddressValue(address)):
                Runtime.crypto(crypto_params).generate_or_load_key_pair(account)

    @staticmethod
    def use_config_from_manifest(project_dir: str):
        """Override zkay configuration with values from the manifest file in project_dir."""
        manifest = Manifest.load(project_dir)
        Manifest.import_manifest_config(manifest)
        Runtime.reset()

    @staticmethod
    def create_dummy_accounts(count: int) -> Union[str, Tuple[str, ...]]:
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
    def _function_ctx(self, trans_sec_size=-1, *, wei_amount: int = 0, name: str = '?'):
        with self.api.api_function_ctx(trans_sec_size, wei_amount) as is_external:
            if is_external:
                zk_print_banner(f'Calling {name}')
                assert self.locals is None
                self.state.clear()
                t_idx = self.tidx.get(name, 0)
                self.tidx[name] = t_idx + 1

            with nullcontext() if not is_external else log_context('transaction', f'{name}_{t_idx}'):
                prev_locals = self.locals
                self.locals = LocalsDict()

                try:
                    yield is_external
                except (ValueError, BlockChainError, RequireException) as e:
                    if is_external and not cfg.is_unit_test:
                        # uncomment to raise errors instead of just printing message (for debugging)
                        # raise e
                        with fail_print():
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
        self.__keystore = {}
        self.__crypto = {}
        self.__prover = Runtime.prover()

        for crypto_params in cfg.all_crypto_params():
            self.__keystore[crypto_params.crypto_name] = Runtime.keystore(crypto_params)
            self.__crypto[crypto_params.crypto_name] = Runtime.crypto(crypto_params)

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
    def keystore(self) -> ZkayKeystoreInterface:
        # Method only exists for compatibility, new code generators only generate calls to get_keystore
        return self.get_keystore(cfg.main_crypto_backend)

    def get_keystore(self, crypto_backend: str):
        return self.__keystore[crypto_backend]

    def get_my_sk(self, crypto_backend: str = cfg.main_crypto_backend) -> PrivateKeyValue:
        return self.__keystore[crypto_backend].sk(self.user_address)

    def get_my_pk(self, crypto_backend: str = cfg.main_crypto_backend) -> PublicKeyValue:
        return self.__keystore[crypto_backend].pk(self.user_address)

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
        self.__contract_handle = self.__conn.connect(self.__project_dir, self.__contract_name, address, self.user_address)

    def transact(self, fname: str, args: List, should_encrypt: List[bool], wei_amount: Optional[int] = None) -> Any:
        return self.__conn.transact(self.__contract_handle, self.__user_addr, fname, args, should_encrypt, wei_amount=wei_amount)

    def call(self, fname: str, args: List, ret_val_constructors: List[Tuple[bool, str, Callable]]):
        retvals = self.__conn.call(self.__contract_handle, self.__user_addr, fname, *args)
        if len(ret_val_constructors) == 1:
            return self.__get_decrypted_retval(retvals, *ret_val_constructors[0])
        else:
            return tuple([self.__get_decrypted_retval(retval, is_cipher, homomorphism, constr)
                          for retval, (is_cipher, homomorphism, constr) in zip(retvals, ret_val_constructors)])

    def __get_decrypted_retval(self, raw_value, is_cipher, crypto_params_name, constructor):
        return self.dec(CipherValue(raw_value, params=CryptoParams(crypto_params_name)), constructor, crypto_backend=crypto_params_name)[0] if is_cipher else constructor(raw_value)

    def get_special_variables(self) -> Tuple[MsgStruct, BlockStruct, TxStruct]:
        assert self.__current_msg is not None and self.__current_block is not None and self.__current_tx is not None
        return self.__current_msg, self.__current_block, self.__current_tx

    def update_special_variables(self, wei_amount: int):
        self.__current_msg, self.__current_block, self.__current_tx = self.__conn.get_special_variables(self.__user_addr, wei_amount)

    def clear_special_variables(self):
        self.__current_msg, self.__current_block, self.__current_tx = None, None, None

    def enc(self, plain: Union[int, AddressValue], target_addr: Optional[AddressValue] = None,
            crypto_backend: str = cfg.main_crypto_backend) -> Tuple[CipherValue, Optional[RandomnessValue]]:
        target_addr = self.__user_addr if target_addr is None else target_addr
        return self.__crypto[crypto_backend].enc(plain, self.__user_addr, target_addr)

    def dec(self, cipher: CipherValue, constr: Callable[[int], Any],
            crypto_backend: str = cfg.main_crypto_backend) -> Tuple[Any, Optional[RandomnessValue]]:
        res = self.__crypto[crypto_backend].dec(cipher, self.__user_addr)
        return constr(res[0]), res[1]

    def do_homomorphic_op(self, op: str, crypto_backend: str, target_addr: AddressValue, *args: Union[CipherValue, int]):
        params = CryptoParams(crypto_backend)
        pk = self.__keystore[params.crypto_name].getPk(target_addr)
        for arg in args:
            if isinstance(arg, CipherValue) and params.crypto_name != arg.params.crypto_name:
                raise ValueError('CipherValues from different crypto backends used in homomorphic operation')

        crypto_inst = self.__crypto[params.crypto_name]
        assert isinstance(crypto_inst, ZkayHomomorphicCryptoInterface)
        result = crypto_inst.do_op(op, pk[:], *args)
        return CipherValue(result, params=params)

    def do_rerand(self, arg: CipherValue, crypto_backend: str, target_addr: AddressValue, data: Dict, rnd_key: str):
        """
        Re-randomizes arg using fresh randomness, which is stored in data[rnd_key] (side-effect!)
        """
        params = CryptoParams(crypto_backend)
        pk = self.__keystore[params.crypto_name].getPk(target_addr)
        crypto_inst = self.__crypto[params.crypto_name]
        assert isinstance(crypto_inst, ZkayHomomorphicCryptoInterface)
        result, rand = crypto_inst.do_rerand(arg, pk[:])
        data[rnd_key] = RandomnessValue(rand, params=params)    # store randomness
        return CipherValue(result, params=params)

    def _req_state_var(self, name: str, *indices, count=0) -> Any:
        if self.__contract_handle is None:
            # TODO check this statically in the type checker
            raise ValueError(f'Cannot read state variable {name} within constructor before it is assigned a value.')

        if count == 0:
            val = self.__conn.req_state_var(self.__contract_handle, name, *indices)
        else:
            val = [self.__conn.req_state_var(self.__contract_handle, name, *indices, i) for i in range(count)]
        return val

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
                val = int_cast(val, bitwidth, signed=False)
            elif bitwidth == 256:
                val %= bn128_scalar_field
        return val

    @staticmethod
    def __serialize_circuit_array(data: dict, target_array: List, target_out_start_idx: int, elem_bitwidths: List[int]):
        idx = target_out_start_idx
        for (name, val), bitwidth in zip(data.items(), elem_bitwidths):
            if isinstance(val, (list, Value)) and not isinstance(val, AddressValue):
                target_array[idx:idx + len(val)] = val[:len(val)] if isinstance(val, CipherValue) else val[:]
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
