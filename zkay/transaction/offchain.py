import inspect
from contextlib import contextmanager
from enum import Enum
from typing import Dict, Union, Callable, Any, Optional, List, Tuple, Type, ContextManager

from zkay.compiler.privacy.manifest import Manifest
from zkay.config import cfg
from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.interface import parse_manifest
from zkay.transaction.types import AddressValue, RandomnessValue, CipherValue, MsgStruct, BlockStruct, TxStruct
from zkay.transaction.runtime import Runtime
from zkay.utils.progress_printer import colored_print, TermColor

bn128_scalar_field = bn128_scalar_field
_bn128_comp_scalar_field = 1 << 252


class RequireException(Exception):
    pass


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
    def __init__(self, project_dir: str, user_addr: AddressValue):
        """
        Create new contract simulator instance.

        :param project_dir: Directory where the zkay contract, the manifest and the prover/verification key files are located
        :param user_addr: From address for all transactions which are issued by this ContractSimulator
        """

        self.project_dir = project_dir
        self.conn = Runtime.blockchain()
        self.crypto = Runtime.crypto()
        self.keystore = Runtime.keystore()
        self.prover = Runtime.prover()

        self.contract_handle = None
        """Handle which refers to the deployed contract, this is passed to the blockchain interface when e.g. issuing transactions."""

        self.user_addr = user_addr
        """From address for all transactions which are issued by this ContractSimulator"""

        # Transaction instance values (reset between transactions)

        self.locals: Optional[Dict[str, Any]] = None
        """Hierarchical dictionary (scopes are managed internally) which holds the currently accessible local variables"""

        self.current_priv_values: Dict[str, Union[int, bool, RandomnessValue]] = {}
        """Dictionary which stores the private circuit values (secret inputs) for the current function (no transitivity)"""

        self.all_priv_values: List[Union[int, bool, RandomnessValue]] = []
        """List which stores all secret circuit inputs for the current transaction in correct order (order of use)"""

        self.current_all_index: Optional[int] = None
        """
        Index which designates where in all_priv_values the secret circuit inputs of the current function should be inserted.
        This is basically private analogue of the start_index parameters which are passed to functions which require verification
        to designate where in the public IO arrays the functions should store/retrieve public circuit inputs/outputs.
        """

        self.state_values: Dict[str, Union[int, bool, CipherValue, AddressValue]] = {}
        """
        Dict which stores stores state variable values. Empty at the beginning of a transaction.
        State variable read: 1. if not in dict -> request from chain and insert into dict, 2. return dict value
        State variable write: store in dict
        """

        self.is_external: Optional[bool] = None
        """
        True whenever simulation is inside a function which was directly (without transitivity) called by the user.
        This is mostly used for some checks (e.g. to prevent the user from calling internal functions), or to change
        function behavior depending on whether a call is external or not (e.g. encrypting parameters or not)
        """

        self.current_msg: Optional[MsgStruct] = None
        self.current_block: Optional[BlockStruct] = None
        self.current_tx: Optional[TxStruct] = None
        """
        Builtin variable (msg, block, tx) values for the current transaction
        """

    @property
    def address(self):
        return self.contract_handle.address

    @staticmethod
    def comp_overflow_checked(val: int):
        """
        Check whether a comparison with value 'val' can be evaluated correctly in the circuit.

        :param val: the value to check
        :raises ValueError:
        """
        if val >= _bn128_comp_scalar_field:
            raise ValueError(f'Value {val} is too large for comparison, circuit would produce wrong results.')
        return val

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

        # python ints are always signed, is expected to be within range of its type
        if isinstance(val, Enum):
            val = val.value
        elif isinstance(val, AddressValue):
            val = int.from_bytes(val.val, byteorder='big')

        if nbits is None: # modulo field prime
            trunc_val = val % bn128_scalar_field
        else:
            trunc_val = val & ((1 << nbits) - 1) # unsigned representation
            if signed and trunc_val & (1 << (nbits - 1)):
                trunc_val -= (1 << nbits) # signed representation

        if constr is not None:
            return constr(trunc_val)
        else:
            return trunc_val

    def _call(self, sec_offset, fct, *args) -> Any:
        with self.call_ctx(sec_offset):
            return fct(*args)

    @staticmethod
    def help(members):
        """Display help for contract functions."""
        signatures = [(fname, str(inspect.signature(sig))) for fname, sig in members]
        print('\n'.join([f'{fname}({sig[5:] if not sig[5:].startswith(",") else sig[7:]}'
                         for fname, sig in signatures
                         if sig.startswith('(self') and not fname.endswith('_check_proof') and not fname.startswith('_')]))

    def get_state(self, name: str, *indices, count=0, is_encrypted=False, val_constructor: Callable[[Any], Any] = lambda x: x):
        """
        Return value of designated state variable, requesting it from blockchain if necessary.

        If the state variable is already in the state_values dict, the cached value will be returned, otherwise
        the value is read from the chain.

        Note: If get_state is called standalone (not as part of transaction simulation),
              it returns decrypted values when is_encrypted=True. Otherwise it returns an encrypted CipherValue.

        :param name: state variable name
        :param indices: if state variable is a (nested) mapping, all index values such that
        :param count: if state variable is an array, this should be the array size
                      (-> all entries will be requested and get_state returns an array)
        :param is_encrypted: should be set to true if the state variable has owner != @all.
        :param val_constructor: if state variable has a type which needs to be wrapped into another type (e.g. address -> AddressValue),
                                this should be the constructor of the wrapper type
        :return: value of the state variable
        """
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
    def default_address() -> AddressValue:
        """Return default wallet address (if supported by backend, otherwise empty address is returned)."""
        return Runtime.blockchain().default_address

    @staticmethod
    def init_key_pair(address: str):
        """Generate/Load keys for the given address."""
        account = AddressValue(address)
        key_pair = Runtime.crypto().generate_or_load_key_pair(account)
        Runtime.keystore().add_keypair(account, key_pair)

    @staticmethod
    def use_config_from_manifest(project_dir: str):
        """Override zkay configuration with values from the manifest file in project_dir."""

        manifest = parse_manifest(project_dir)

        # Check if zkay version matches
        if manifest[Manifest.zkay_version] != cfg.zkay_version:
            with colored_print(TermColor.WARNING):
                print(f'Zkay version in manifest ({manifest[Manifest.zkay_version]}) does not match current zkay version ({cfg.zkay_version})\n'
                      f'Compilation or integrity check with deployed bytecode might fail due to version differences')

        cfg.override_solc(manifest[Manifest.solc_version])
        cfg.deserialize(manifest[Manifest.zkay_options])
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
            ContractSimulator.init_key_pair(account)
        if len(accounts) == 1:
            return accounts[0]
        else:
            return accounts

    @contextmanager
    def call_ctx(self, sec_offset) -> ContextManager:
        """Return context manager which sets the correct current_all_index for the given sec_offset during its lifetime."""
        old_priv_values, old_all_idx = self.current_priv_values, self.current_all_index
        self.current_priv_values = {}
        self.current_all_index += sec_offset
        yield
        self.current_priv_values, self.current_all_index = old_priv_values, old_all_idx

    @contextmanager
    def scope(self) -> ContextManager:
        """Return context manager which manages the lifetime of a local scope."""
        self.locals.push_scope()
        yield
        self.locals.pop_scope()


class FunctionCtx:
    """
    Context manager which manages the lifetime of transaction instance variables.
    """

    def __init__(self, v: ContractSimulator, trans_sec_size, *, value: int = 0):
        self.v = v
        self.was_external = None
        self.trans_sec_size = trans_sec_size
        self.value = value
        self.prev_locals = None

    def __enter__(self):
        self.was_external = self.v.is_external
        if self.v.is_external is None:
            assert self.v.locals is None
            self.v.is_external = True
            self.v.state_values.clear()
            self.v.all_priv_values = [0 for _ in range(self.trans_sec_size)]
            self.v.current_all_index = 0
            self.v.current_priv_values.clear()
            self.v.current_msg, self.v.current_block, self.v.current_tx = self.v.conn.get_special_variables(self.v.user_addr, self.value)
        else:
            self.v.is_external = False
        self.prev_locals = self.v.locals
        self.v.locals = LocalsDict()

    def __exit__(self, exec_type, exec_value, traceback):
        self.v.locals = self.prev_locals
        if self.v.is_external:
            assert self.v.locals is None
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
