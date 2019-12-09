import json
import os
import shutil
import tempfile
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List, Union

from eth_tester import PyEVMBackend, EthereumTester
from web3 import Web3

from zkay.compiler.privacy import library_contracts
from zkay.compiler.solidity.compiler import compile_solidity_json
from zkay.config import cfg, debug_print
from zkay.transaction.interface import Manifest, ZkayBlockchainInterface
from zkay.transaction.types import PublicKeyValue, AddressValue, MsgStruct, BlockStruct, TxStruct
from zkay.utils.helpers import get_contract_names, without_extension
from zkay.utils.progress_printer import colored_print, TermColor

max_gas_limit = 10000000


class Web3Blockchain(ZkayBlockchainInterface):
    def __init__(self) -> None:
        super().__init__()

        self.w3 = self._create_w3_instance()

        self.verifiers_for_uuid: Dict[str, Dict[str, AddressValue]] = {}

    @staticmethod
    def compile_contract(sol_filename: str, contract_name: str, libs: Optional[Dict] = None):
        solp = Path(sol_filename)
        jout = compile_solidity_json(sol_filename, libs, optimizer_runs=10)['contracts'][solp.name][contract_name]
        return {
            'abi': json.loads(jout['metadata'])['output']['abi'],
            'bin': jout['evm']['bytecode']['object'],
            'deployed_bin': jout['evm']['deployedBytecode']['object']
        }

    def deploy_contract(self, sender: str, contract_interface, *args, value: Optional[int] = None):
        if args is None:
            args = []

        contract = self.w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )

        tx_receipt = self._transact(contract, sender, 'constructor', *args, value=value)
        contract = self.w3.eth.contract(
            address=tx_receipt.contractAddress, abi=contract_interface['abi']
        )
        return contract

    def get_special_variables(self, sender: AddressValue, value: int = 0) -> Tuple[MsgStruct, BlockStruct, TxStruct]:
        block = self.w3.eth.getBlock('pending')
        return MsgStruct(sender, value), \
               BlockStruct(AddressValue(self.w3.eth.coinbase), block['difficulty'], block['gasLimit'], block['number'], block['timestamp']),\
               TxStruct(self.w3.eth.gasPrice, sender)

    @abstractmethod
    def _create_w3_instance(self) -> Web3:
        pass

    def _pki_verifier_addresses(self, sender: str, manifest) -> Dict[str, AddressValue]:
        uuid = manifest[Manifest.uuid]
        if uuid not in self.verifiers_for_uuid:
            # Deploy verification contracts if not already done
            vf = {}
            for verifier_name in manifest[Manifest.verifier_names].values():
                filename = os.path.join(manifest[Manifest.project_dir], f'{verifier_name}.sol')
                cout = self.compile_contract(filename, verifier_name, self.lib_addresses)
                vf[verifier_name] = AddressValue(self.deploy_contract(sender, cout).address)
            self.verifiers_for_uuid[uuid] = vf
        ret = self.verifiers_for_uuid[uuid].copy()
        ret[cfg.pki_contract_name] = AddressValue(self.pki_contract.address)
        return ret

    def _my_address(self) -> AddressValue:
        return AddressValue(self.w3.eth.defaultAccount)

    def _get_balance(self, address: str) -> int:
        return self.w3.eth.getBalance(address)

    def _req_public_key(self, address: str) -> PublicKeyValue:
        return PublicKeyValue(self._req_state_var(self.pki_contract, 'getPk', address, sender=self.my_address.val))

    def _announce_public_key(self, address: str, pk: Tuple[int, ...]):
        return self._transact(self.pki_contract, address, 'announcePk', pk)

    def _req_state_var(self, contract_handle, name: str, *indices, sender: str) -> Any:
        return contract_handle.functions[name](*indices).call({'from': sender})

    def _transact(self, contract_handle, sender: str, function: str, *actual_params, value: Optional[int] = None) -> Any:
        fobj = contract_handle.constructor if function == 'constructor' else contract_handle.functions[function]
        tx = {'from': sender, 'gas': max_gas_limit}
        if value:
            tx['value'] = value
        tx_hash = fobj(*actual_params).transact(tx)
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        if tx_receipt['status'] == 0:
            raise Exception("Transaction failed")
        debug_print(f"Consumed gas: {tx_receipt['gasUsed']}")
        return tx_receipt

    def _deploy(self, manifest, sender: str, contract: str, *actual_args, value: Optional[int] = None):
        filename = self.__hardcode_external_contracts(os.path.join(manifest[Manifest.project_dir], manifest[Manifest.contract_filename]),
                                                      self._pki_verifier_addresses(sender, manifest))
        cout = self.compile_contract(filename, contract)
        return self.deploy_contract(sender, cout, *actual_args, value=value)

    def _deploy_libraries(self, sender: str):
        # Compile and deploy global libraries
        with tempfile.TemporaryDirectory() as tmpdir:
            pki_sol = os.path.join(tmpdir, f'{cfg.pki_contract_name}.sol')
            with open(pki_sol, 'w') as f:
                f.write(library_contracts.get_pki_contract())

            verify_sol = os.path.join(tmpdir, 'verify_libs.sol')
            with open(verify_sol, 'w') as f:
                f.write(library_contracts.get_verify_libs_code())

            self.pki_contract = self.deploy_contract(sender, self.compile_contract(pki_sol, cfg.pki_contract_name))
            self.lib_addresses = {
                f'BN256G2': self.deploy_contract(sender, self.compile_contract(verify_sol, 'BN256G2')).address,
            }

    def _connect(self, manifest, contract: str, address: str) -> Any:
        filename = os.path.join(manifest[Manifest.project_dir], manifest[Manifest.contract_filename])
        cout = self.compile_contract(filename, contract)
        return self.w3.eth.contract(
            address=address, abi=cout['abi']
        )

    def _verify_contract_integrity(self, address: str, sol_filename: str, *,
                                   libraries: Dict = None, contract_name: str = None, is_library: bool = False):
        if contract_name is None:
            contract_name = get_contract_names(sol_filename)[0]
        actual_byte_code = self.__normalized_hex(self.w3.eth.getCode(address))
        cout = self.compile_contract(sol_filename, contract_name, libs=libraries)
        expected_byte_code = self.__normalized_hex(cout['deployed_bin'])

        if is_library:
            # https://github.com/ethereum/solidity/issues/7101
            expected_byte_code = expected_byte_code[:2] + self.__normalized_hex(address) + expected_byte_code[42:]

        if actual_byte_code != expected_byte_code:
            raise ValueError(f'Deployed contract at address {address} does not match local contract {sol_filename}')
        debug_print(f'Contract@{address} matches {sol_filename[sol_filename.rfind("/")+1:]}:{contract_name}')

    def _verify_library_integrity(self, libraries: List[Tuple[str, str]], contract_with_libs_addr: str, sol_with_libs_filename: str) -> Dict[str, str]:
        cname = get_contract_names(sol_with_libs_filename)[0]
        actual_code = self.__normalized_hex(self.w3.eth.getCode(contract_with_libs_addr))
        code_with_placeholders = self.__normalized_hex(self.compile_contract(sol_with_libs_filename, cname)['deployed_bin'])

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
                self._verify_contract_integrity(lib_address, lib_sol, contract_name=lib_name, is_library=True)
                addresses[lib_name] = lib_address
        return addresses

    def _verify_zkay_contract_integrity(self, address: str, sol_file: str, pki_verifier_addresses):
        sol_file = self.__hardcode_external_contracts(sol_file, pki_verifier_addresses)
        self._verify_contract_integrity(address, sol_file)

    @staticmethod
    def __hardcode_external_contracts(input_filename, pki_verifier_addresses):
        with open(input_filename) as f:
            c = f.read()
        for key, val in pki_verifier_addresses.items():
            c = c.replace(f'{key}(0)', f'{key}({val.val})')

        output_filename = f'{without_extension(input_filename)}.inst.sol'
        with open(output_filename, 'w') as f:
            f.write(c)
        return output_filename

    def __normalized_hex(self, val: Union[str, bytes]) -> str:
        if not isinstance(val, str):
            val = val.hex()
        val = val[2:] if val.startswith('0x') else val
        return val.lower()


class Web3TesterBlockchain(Web3Blockchain):
    def __init__(self) -> None:
        self.eth_tester = None
        super().__init__()
        self.deploy_libraries(self.my_address)
        self.next_acc_idx = 1

    def _create_w3_instance(self) -> Web3:
        genesis_overrides = {'gas_limit': int(max_gas_limit * 1.2)}
        custom_genesis_params = PyEVMBackend._generate_genesis_params(overrides=genesis_overrides)
        self.eth_tester = EthereumTester(backend=PyEVMBackend(genesis_parameters=custom_genesis_params))
        w3 = Web3(Web3.EthereumTesterProvider(self.eth_tester))
        w3.eth.defaultAccount = w3.eth.accounts[0]
        return w3

    def create_test_accounts(self, count: int) -> Tuple:
        accounts = self.w3.eth.accounts
        if len(accounts[self.next_acc_idx:]) < count:
            raise ValueError(f'Can have at most {len(accounts)-1} dummy accounts in total')
        dummy_accounts = tuple(accounts[self.next_acc_idx:self.next_acc_idx + count])
        self.next_acc_idx += count
        return dummy_accounts
