from zkay_ast.ast import Identifier


class UsedContractLegacy:

    def __init__(self, filename: str, contract_name: str, state_variable_name: str):
        self.filename = filename
        self.contract_name = contract_name
        self.state_variable_name = state_variable_name

    def __eq__(self, other):
        if isinstance(other, UsedContractLegacy):
            return \
                self._as_tuple() == other._as_tuple()
        else:
            return False

    def _as_tuple(self):
        return self.filename, self.contract_name, self.state_variable_name

    def __hash__(self):
        return hash(str(self._as_tuple()))


def get_contract_instance_idf(type_name: str) -> Identifier:
    return Identifier(f'{type_name}_inst')
