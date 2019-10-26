from typing import List, Union, Tuple

from zkay_ast.ast import Parameter, Expression


class ProofArgument:

    def __init__(self, ast: Union[Parameter, Expression]):
        self.ast = ast


class FromZok(ProofArgument):

    def __init__(self, expr: Expression):
        super().__init__(expr)


class ParameterCheck(ProofArgument):

    def __init__(self, p: Parameter):
        super().__init__(p)


class FromSolidity(ProofArgument):

    def __init__(self, expr: Expression):
        super().__init__(expr)


class ProofHelper:

    def __init__(self):
        self.zok_arguments: List[str] = []
        self.zok_params: List[str] = []
        self.param_docs: List[Tuple[str, str]] = []
        self.public_params = []

        self.statements: List[str] = []

        self.proof_arguments: List[ProofArgument] = []

    def add_private_key(self, base_name: str):
        # private key of "me"
        key = f'{base_name}SK'
        self.zok_params += [f'private field {key}']
        return key

    def add_randomness(self, base_name: str):
        randomness = f'{base_name}R'
        self.zok_params += [f'private field {randomness}']
        return randomness

    def add_value(self, base_name: str):
        value = f'{base_name}Value'
        self.zok_params += [f'private field {value}']
        return value

    def add_public_param(self, name, ast: Union[Parameter, Expression]):
        self.param_docs += [[name, str(ast)]]
        self.zok_params += [f'private field {name}']
        self.public_params += [name]
