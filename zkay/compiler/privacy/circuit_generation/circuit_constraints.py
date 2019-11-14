from zkay.zkay_ast.ast import HybridArgumentIdf, Expression, LocationExpr


class CircuitStatement:
    pass


class TempVarDecl(CircuitStatement):
    def __init__(self, lhs: HybridArgumentIdf, expr: Expression):
        self.lhs = lhs
        self.expr = expr


class CircAssignment(CircuitStatement):
    def __init__(self, lhs: LocationExpr, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs


class EncConstraint(CircuitStatement):
    def __init__(self, plain: HybridArgumentIdf, rnd: HybridArgumentIdf, pk: HybridArgumentIdf, cipher: HybridArgumentIdf):
        self.plain = plain
        self.rnd = rnd
        self.pk = pk
        self.cipher = cipher


class EqConstraint(CircuitStatement):
    def __init__(self, tgt: HybridArgumentIdf, val: HybridArgumentIdf):
        self.tgt = tgt
        self.val = val