from zkay.zkay_ast.ast import Identifier


def get_contract_instance_idf(type_name: str) -> Identifier:
    return Identifier(f'{type_name}_inst')
