from zkay_ast.ast import AnnotatedTypeName, Identifier


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


class UsedContract:

    def __init__(self, filename: str, contract_type: AnnotatedTypeName, state_variable_idf: Identifier):
        self.filename = filename
        self.contract_type = contract_type
        self.state_variable_idf = state_variable_idf

    def __eq__(self, other):
        if isinstance(other, UsedContract):
            return self._as_tuple() == other._as_tuple()
        else:
            return False

    def _as_tuple(self):
        return self.filename, self.contract_type.type_name.code(), self.state_variable_idf.name

    def __hash__(self):
        return hash(str(self._as_tuple()))