from enum import Enum


class Homomorphism(Enum):
    NON_HOMOMORPHIC = ('<>', 'unhom')
    ADDITIVE = ('<+>', 'addhom')

    def __init__(self, type_annotation: str, rehom_expr_name: str):
        self.type_annotation = type_annotation
        self.rehom_expr_name = rehom_expr_name

    def __str__(self):
        return self.type_annotation if self != Homomorphism.NON_HOMOMORPHIC else ''
