import os

from compiler.privacy.circuit_generation.backends.zokrates_generator import ZokratesGenerator
from compiler.privacy.proving_schemes.gm17 import ProvingSchemeGm17
from compiler.privacy.proving_schemes.proving_scheme import ProvingScheme
from compiler.privacy.transformer.zkay_transformer import transform_ast, pki_contract_name
from zkay_ast.ast import AST


def compile_zkay(ast: AST, output_dir: str, filename: str):
    ast, zkt = transform_ast(ast)

    # Write public contract file
    with open(os.path.join(output_dir, filename), 'w') as f:
        f.write(ast.code())

    # Write pki contract
    with open(os.path.join(output_dir, f'{pki_contract_name}.sol'), 'w') as f:
        f.write(pki_contract)

    # Write library contract
    with open(os.path.join(output_dir, ProvingScheme.verify_libs_contract_filename), 'w') as f:
        f.write(ProvingScheme.get_library_code())

    # Generate circuits and corresponding verification contracts
    cg = ZokratesGenerator(ast, list(zkt.circuit_generators.values()), ProvingSchemeGm17(), output_dir)
    cg.generate_circuits()


pki_contract = '''\
pragma solidity ^0.5;

contract PublicKeyInfrastructure {
    mapping(address => uint) pks;
    mapping(address => bool) hasAnnounced;

    function announcePk(uint pk) public {
        pks[msg.sender] = pk;
        hasAnnounced[msg.sender] = true;
    }

    function getPk(address a) public view returns(uint) {
        require(hasAnnounced[a]);
        return pks[a];
    }
}\
'''