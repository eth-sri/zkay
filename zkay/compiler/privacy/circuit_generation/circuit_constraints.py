from typing import List, Optional

from zkay.zkay_ast.ast import HybridArgumentIdf, Expression, LocationExpr, ConstructorOrFunctionDefinition


class CircuitStatement:
    pass


class CircComment(CircuitStatement):
    def __init__(self, text: str):
        super().__init__()
        self.text = text


class CircIndentBlock(CircuitStatement):
    def __init__(self, name: str, statements: List[CircuitStatement]):
        super().__init__()
        self.name = name
        self.statements = statements


class CircCall(CircuitStatement):
    def __init__(self, fct: ConstructorOrFunctionDefinition):
        super().__init__()
        self.fct = fct


class CircVarDecl(CircuitStatement):
    def __init__(self, lhs: HybridArgumentIdf, expr: Expression):
        super().__init__()
        self.lhs = lhs
        self.expr = expr


class CircGuardModification(CircuitStatement):
    def __init__(self, new_cond: Optional[HybridArgumentIdf], is_true: Optional[bool] = None):
        super().__init__()
        self.new_cond = new_cond
        self.is_true = is_true

    @staticmethod
    def add_guard(new_cond: HybridArgumentIdf, is_true: bool):
        return CircGuardModification(new_cond, is_true)

    @staticmethod
    def pop_guard():
        return CircGuardModification(None)


class CircEncConstraint(CircuitStatement):
    def __init__(self, plain: HybridArgumentIdf, rnd: HybridArgumentIdf, pk: HybridArgumentIdf, cipher: HybridArgumentIdf, is_dec: bool):
        super().__init__()
        self.plain = plain
        self.rnd = rnd
        self.pk = pk
        self.cipher = cipher
        self.is_dec = is_dec # True if this is an inverted decryption


class CircEqConstraint(CircuitStatement):
    def __init__(self, tgt: HybridArgumentIdf, val: HybridArgumentIdf):
        super().__init__()
        self.tgt = tgt
        self.val = val
