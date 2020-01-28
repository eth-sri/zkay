from zkay.zkay_ast.ast import Identifier


def get_contract_instance_idf(type_name: str) -> Identifier:
    """
    Return an identifier referring to the address variable of verification contract of type 'type_name'
    :param type_name: name of the unqualified verification contract type
    :return: new identifier
    """
    return Identifier(f'{type_name}_inst')
