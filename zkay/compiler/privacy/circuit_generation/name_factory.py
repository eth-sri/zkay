from typing import Optional

from zkay.zkay_ast.ast import TypeName, HybridArgType, Expression, HybridArgumentIdf


class BaseNameFactory:
    def __init__(self, base_name: str):
        self.base_name = base_name
        self.count = 0

    def get_new_name(self, t: TypeName, inc=True) -> str:
        if t == TypeName.key_type():
            postfix = 'key'
        elif t == TypeName.cipher_type():
            postfix = 'cipher'
        else:
            postfix = 'plain'
        name = f'{self.base_name}{self.count}_{postfix}'
        if inc:
            self.count += 1
        return name


class NameFactory(BaseNameFactory):
    def __init__(self, base_name: str, arg_type: HybridArgType):
        super().__init__(base_name)
        self.arg_type = arg_type
        self.size = 0
        self.idfs = []

    def get_new_idf(self, t: TypeName, priv_expr: Optional[Expression] = None) -> HybridArgumentIdf:
        name = self.get_new_name(t)
        idf = HybridArgumentIdf(name, t, self.arg_type, priv_expr)
        self.size += t.size_in_uints
        self.idfs.append(idf)
        return idf

    def add_idf(self, name: str, t: TypeName):
        idf = HybridArgumentIdf(name, t, self.arg_type)
        self.count += 1
        self.size += t.size_in_uints
        self.idfs.append(idf)
        return idf
