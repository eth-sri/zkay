import json
import os
import tempfile
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List, Union

from eth_tester import PyEVMBackend, EthereumTester
from web3 import Web3

from zkay.compiler.privacy import library_contracts
from zkay.compiler.solidity.compiler import compile_solidity_json
from zkay.config import cfg, zk_print
from zkay.transaction.interface import ZkayBlockchainInterface, IntegrityError, BlockChainError, \
    TransactionFailedException
from zkay.transaction.types import PublicKeyValue, AddressValue, MsgStruct, BlockStruct, TxStruct
from zkay.utils.helpers import get_contract_names, without_extension, save_to_file
from zkay.zkay_ast.process_ast import get_verification_contract_names

max_gas_limit = 10000000


class Web3Blockchain(ZkayBlockchainInterface):
    def __init__(self) -> None:
        super().__init__()
        self.w3 = self._create_w3_instance()
        if not self.w3.isConnected():
            raise BlockChainError(f'Failed to connect to blockchain: {self.w3.provider}')

        self.verifiers_for_uuid: Dict[str, Dict[str, AddressValue]] = {}
        self._pki_contract = None
        self._lib_addresses = None

    @property
    def pki_contract(self):
        if self._pki_contract is None:
            self._connect_libraries()
        return self._pki_contract

    @property
    def lib_addresses(self) -> Dict:
        if self._lib_addresses is None:
            self._connect_libraries()
        return self._lib_addresses

    @staticmethod
    def compile_contract(sol_filename: str, contract_name: str, libs: Optional[Dict] = None):
        solp = Path(sol_filename)
        jout = compile_solidity_json(sol_filename, libs, optimizer_runs=cfg.opt_solc_optimizer_runs)['contracts'][solp.name][contract_name]
        return {
            'abi': json.loads(jout['metadata'])['output']['abi'],
            'bin': jout['evm']['bytecode']['object'],
            'deployed_bin': jout['evm']['deployedBytecode']['object']
        }

    def deploy_solidity_contract(self, sol_filename: str, contract_name: Optional[str], sender: Union[bytes, str]) -> str:
        contract_name = get_contract_names(sol_filename)[0] if contract_name is None else contract_name
        contract = self._deploy_contract(sender, self.compile_contract(sol_filename, contract_name))
        return str(contract.address)

    def get_special_variables(self, sender: AddressValue, wei_amount: int = 0) -> Tuple[MsgStruct, BlockStruct, TxStruct]:
        block = self.w3.eth.getBlock('pending')
        return MsgStruct(sender, wei_amount), \
               BlockStruct(AddressValue(self.w3.eth.coinbase), block['difficulty'], block['gasLimit'], block['number'], block['timestamp']),\
               TxStruct(self.w3.eth.gasPrice, sender)

    @abstractmethod
    def _create_w3_instance(self) -> Web3:
        pass

    def _default_address(self) -> Union[None, bytes, str]:
        if cfg.blockchain_default_account is None:
            return None
        elif isinstance(cfg.blockchain_default_account, int):
            return self.w3.eth.accounts[cfg.blockchain_default_account]
        else:
            return cfg.blockchain_default_account

    def _get_balance(self, address: Union[bytes, str]) -> int:
        return self.w3.eth.getBalance(address)

    def _req_public_key(self, address: Union[bytes, str]) -> PublicKeyValue:
        return PublicKeyValue(self._req_state_var(self.pki_contract, 'getPk', address))

    def _announce_public_key(self, address: Union[bytes, str], pk: Tuple[int, ...]) -> Any:
        return self._transact(self.pki_contract, address, 'announcePk', pk)

    def _req_state_var(self, contract_handle, name: str, *indices) -> Any:
        try:
            return contract_handle.functions[name](*indices).call()
        except Exception as e:
            raise BlockChainError(e.args)

    def _transact(self, contract_handle, sender: Union[bytes, str], function: str, *actual_params, wei_amount: Optional[int] = None) -> Any:
        try:
            fobj = contract_handle.constructor if function == 'constructor' else contract_handle.functions[function]
            gas_amount = self._gas_heuristic(sender, fobj(*actual_params))
            tx = {'from': sender, 'gas': gas_amount}
            if wei_amount:
                tx['value'] = wei_amount
            tx_hash = fobj(*actual_params).transact(tx)
            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        except Exception as e:
            raise BlockChainError(e.args)

        if tx_receipt['status'] == 0:
            raise TransactionFailedException("Transaction failed")
        zk_print(f"Consumed gas: {tx_receipt['gasUsed']}")
        return tx_receipt

    def _deploy(self, project_dir: str, sender: Union[bytes, str], contract: str, *actual_args, wei_amount: Optional[int] = None) -> Any:
        with open(os.path.join(project_dir, 'contract.zkay')) as f:
            verifier_names = get_verification_contract_names(f.read())

        # Deploy verification contracts if not already done
        external_contract_addresses =  self._deploy_dependencies(sender, project_dir, verifier_names)
        filename = self.__hardcode_external_contracts(os.path.join(project_dir, 'contract.sol'),
                                                      external_contract_addresses)
        cout = self.compile_contract(filename, contract)
        handle = self._deploy_contract(sender, cout, *actual_args, wei_amount=wei_amount)
        zk_print(f'Deployed contract "{contract}" at address "{handle.address}"')
        return handle

    def _deploy_contract(self, sender: Union[bytes, str], contract_interface, *args, wei_amount: Optional[int] = None):
        if args is None:
            args = []

        contract = self.w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )

        tx_receipt = self._transact(contract, sender, 'constructor', *args, wei_amount=wei_amount)
        contract = self.w3.eth.contract(
            address=tx_receipt.contractAddress, abi=contract_interface['abi']
        )
        return contract

    def _deploy_dependencies(self, sender: Union[bytes, str], project_dir: str, verifier_names: List[str]) -> Dict[str, AddressValue]:
        # Deploy verification contracts if not already done
        vf = {}
        for verifier_name in verifier_names:
            filename = os.path.join(project_dir, f'{verifier_name}.sol')
            cout = self.compile_contract(filename, verifier_name, self.lib_addresses)
            vf[verifier_name] = AddressValue(self._deploy_contract(sender, cout).address)
        vf[cfg.pki_contract_name] = AddressValue(self.pki_contract.address)
        return vf

    def _connect_libraries(self):
        if not cfg.blockchain_pki_address or not cfg.blockchain_crypto_lib_addresses:
            raise BlockChainError('Must specify pki and all crypto library addresses in config.')
        lib_addresses = [addr.strip() for addr in cfg.blockchain_crypto_lib_addresses.split(',')]
        if len(lib_addresses) != len(cfg.external_crypto_lib_names):
            raise BlockChainError('Must specify all crypto library addresses in config\n'
                                  f'Expected {len(cfg.external_crypto_lib_names)} was {len(lib_addresses)}')

        with cfg.library_compilation_environment():
            with tempfile.TemporaryDirectory() as tmpdir:
                pki_sol = save_to_file(tmpdir, f'{cfg.pki_contract_name}.sol', library_contracts.get_pki_contract())
                self._pki_contract = self._verify_contract_integrity(cfg.blockchain_pki_address, pki_sol, contract_name=cfg.pki_contract_name)

                verify_sol = save_to_file(tmpdir, 'verify_libs.sol', library_contracts.get_verify_libs_code())
                self._lib_addresses = {}
                for lib, addr in zip(cfg.external_crypto_lib_names, lib_addresses):
                    out = self._verify_contract_integrity(addr, verify_sol, contract_name=lib, is_library=True)
                    self._lib_addresses[lib] = out.address

    def _connect(self, project_dir: str, contract: str, address: Union[bytes, str]) -> Any:
        filename = os.path.join(project_dir, 'contract.sol')
        cout = self.compile_contract(filename, contract)
        return self.w3.eth.contract(
            address=address, abi=cout['abi']
        )

    def _verify_contract_integrity(self, address: Union[bytes, str], sol_filename: str, *,
                                   libraries: Dict = None, contract_name: str = None, is_library: bool = False) -> Any:
        if isinstance(address, bytes):
            address = self.w3.toChecksumAddress(address)

        if contract_name is None:
            contract_name = get_contract_names(sol_filename)[0]
        actual_byte_code = self.__normalized_hex(self.w3.eth.getCode(address))
        if not actual_byte_code:
            raise IntegrityError(f'Expected contract {contract_name} is not deployed at address {address}')

        cout = self.compile_contract(sol_filename, contract_name, libs=libraries)
        expected_byte_code = self.__normalized_hex(cout['deployed_bin'])

        if is_library:
            # https://github.com/ethereum/solidity/issues/7101
            expected_byte_code = expected_byte_code[:2] + self.__normalized_hex(address) + expected_byte_code[42:]

        if actual_byte_code != expected_byte_code:
            raise IntegrityError(f'Deployed contract at address {address} does not match local contract {sol_filename}')
        zk_print(f'Contract@{address} matches {sol_filename[sol_filename.rfind("/") + 1:]}:{contract_name}')

        return self.w3.eth.contract(
            address=address, abi=cout['abi']
        )

    def _verify_library_integrity(self, libraries: List[Tuple[str, str]], contract_with_libs_addr: str, sol_with_libs_filename: str) -> Dict[str, str]:
        cname = get_contract_names(sol_with_libs_filename)[0]
        actual_code = self.__normalized_hex(self.w3.eth.getCode(contract_with_libs_addr))
        if not actual_code:
            raise IntegrityError(f'Expected contract {cname} is not deployed at address {contract_with_libs_addr}')
        code_with_placeholders = self.__normalized_hex(self.compile_contract(sol_with_libs_filename, cname)['deployed_bin'])

        if len(actual_code) != len(code_with_placeholders):
            raise IntegrityError(f'Local code of contract {cname} has different length than remote contract')

        addresses = {}
        for lib_name, lib_sol in libraries:
            # Compute placeholder according to
            # https://solidity.readthedocs.io/en/v0.5.13/using-the-compiler.html#using-the-commandline-compiler
            hash = self.w3.solidityKeccak(['string'], [f'{lib_sol[lib_sol.rfind("/") + 1:]}:{lib_name}'])
            placeholder = f'__${self.__normalized_hex(hash)[:34]}$__'

            # Retrieve concrete address in deployed code at placeholder offset in local code and verify library contract integrity
            lib_address_offset = code_with_placeholders.find(placeholder)
            if lib_address_offset != -1:
                lib_address = self.w3.toChecksumAddress(actual_code[lib_address_offset:lib_address_offset+40])
                with cfg.library_compilation_environment():
                    self._verify_contract_integrity(lib_address, lib_sol, contract_name=lib_name, is_library=True)
                addresses[lib_name] = lib_address
        return addresses

    def _verify_zkay_contract_integrity(self, address: str, sol_file: str, pki_verifier_addresses: Dict):
        sol_file = self.__hardcode_external_contracts(sol_file, pki_verifier_addresses)
        self._verify_contract_integrity(address, sol_file)

    def __hardcode_external_contracts(self, input_filename, pki_verifier_addresses):
        with open(input_filename) as f:
            c = f.read()
        for key, val in pki_verifier_addresses.items():
            c = c.replace(f'{key}(0)', f'{key}({self.w3.toChecksumAddress(val.val)})')

        output_filename = f'{without_extension(input_filename)}.inst.sol'
        with open(output_filename, 'w') as f:
            f.write(c)
        return output_filename

    def __normalized_hex(self, val: Union[str, bytes]) -> str:
        if not isinstance(val, str):
            val = val.hex()
        val = val[2:] if val.startswith('0x') else val
        return val.lower()

    def _gas_heuristic(self, sender, tx) -> int:
        limit = self.w3.eth.getBlock('latest')['gasLimit']
        estimate = tx.estimateGas({'from': sender, 'gas': limit})
        return min(int(estimate * 1.2), limit)


class Web3TesterBlockchain(Web3Blockchain):
    def __init__(self) -> None:
        self.eth_tester = None
        super().__init__()
        self.next_acc_idx = 1

    @classmethod
    def is_debug_backend(cls) -> bool:
        return True

    def _connect_libraries(self):
        sender = self.w3.eth.accounts[0]
        # Since eth-tester is not persistent -> always automatically deploy libraries
        with cfg.library_compilation_environment():
            with tempfile.TemporaryDirectory() as tmpdir:
                pki_sol = save_to_file(tmpdir, f'{cfg.pki_contract_name}.sol', library_contracts.get_pki_contract())
                self._pki_contract = self._deploy_contract(sender, self.compile_contract(pki_sol, cfg.pki_contract_name))
                zk_print(f'Deployed pki contract at address "{self.pki_contract.address}"')

                verify_sol = save_to_file(tmpdir, 'verify_libs.sol', library_contracts.get_verify_libs_code())
                self._lib_addresses = {}
                for lib in cfg.external_crypto_lib_names:
                    out = self._deploy_contract(sender, self.compile_contract(verify_sol, lib))
                    self._lib_addresses[lib] = out.address
                    zk_print(f'Deployed crypto lib {lib} at address "{out.address}"')

    def _create_w3_instance(self) -> Web3:
        genesis_overrides = {'gas_limit': int(max_gas_limit * 1.2)}
        custom_genesis_params = PyEVMBackend._generate_genesis_params(overrides=genesis_overrides)
        self.eth_tester = EthereumTester(backend=PyEVMBackend(genesis_parameters=custom_genesis_params))
        w3 = Web3(Web3.EthereumTesterProvider(self.eth_tester))
        return w3

    def create_test_accounts(self, count: int) -> Tuple:
        accounts = self.w3.eth.accounts
        if len(accounts[self.next_acc_idx:]) < count:
            raise ValueError(f'Can have at most {len(accounts)-1} dummy accounts in total')
        dummy_accounts = tuple(accounts[self.next_acc_idx:self.next_acc_idx + count])
        self.next_acc_idx += count
        return dummy_accounts

    def _gas_heuristic(self, sender, tx) -> int:
        return max_gas_limit


class Web3IpcBlockchain(Web3Blockchain):
    def _create_w3_instance(self) -> Web3:
        assert cfg.blockchain_node_uri is None or isinstance(cfg.blockchain_node_uri, str)
        return Web3(Web3.IPCProvider(cfg.blockchain_node_uri))


class Web3WebsocketBlockchain(Web3Blockchain):
    def _create_w3_instance(self) -> Web3:
        assert cfg.blockchain_node_uri is None or isinstance(cfg.blockchain_node_uri, str)
        return Web3(Web3.WebsocketProvider(cfg.blockchain_node_uri))


class Web3HttpBlockchain(Web3Blockchain):
    def _create_w3_instance(self) -> Web3:
        assert cfg.blockchain_node_uri is None or isinstance(cfg.blockchain_node_uri, str)
        return Web3(Web3.HTTPProvider(cfg.blockchain_node_uri))


class Web3HttpGanacheBlockchain(Web3HttpBlockchain):
    def __init__(self) -> None:
        super().__init__()
        self.next_acc_idx = 1

    @classmethod
    def is_debug_backend(cls) -> bool:
        return True

    def create_test_accounts(self, count: int) -> Tuple:
        accounts = self.w3.eth.accounts
        if len(accounts[self.next_acc_idx:]) < count:
            raise ValueError(f'Can have at most {len(accounts)-1} dummy accounts in total')
        dummy_accounts = tuple(accounts[self.next_acc_idx:self.next_acc_idx + count])
        self.next_acc_idx += count
        return dummy_accounts

    def _gas_heuristic(self, sender, tx) -> int:
        return self.w3.eth.getBlock('latest')['gasLimit']


class Web3CustomBlockchain(Web3Blockchain):
    def _create_w3_instance(self) -> Web3:
        assert isinstance(cfg.blockchain_node_uri, Web3)
        return cfg.blockchain_node_uri
