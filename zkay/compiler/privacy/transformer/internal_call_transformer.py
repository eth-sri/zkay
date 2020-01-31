from collections import OrderedDict
from typing import List, Dict

from zkay.config import cfg
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.zkay_ast.ast import ConstructorOrFunctionDefinition, IdentifierExpr, NumberLiteralExpr


def transform_internal_calls(hybrid_fcts: List[ConstructorOrFunctionDefinition], cgens: Dict[ConstructorOrFunctionDefinition, CircuitHelper]):
    for fct in hybrid_fcts:
        glob_keys = OrderedDict()
        circuit = cgens[fct]
        circuit.trans_in_size, circuit.trans_out_size, circuit.trans_priv_size = _compute_transitive_circuit_io_sizes(cgens, fct, glob_keys)
        circuit._global_keys = glob_keys
    for fct in hybrid_fcts:
        circuit = cgens[fct]
        i, o, p = 0, 0, 0
        for fc in circuit.function_calls_with_verification:
            fdef = fc.func.target
            fc.sec_start_offset = circuit.priv_in_size + p
            fc.args += [IdentifierExpr(cfg.zk_in_name),
                        IdentifierExpr(f'{cfg.zk_in_name}start_idx').binop('+', NumberLiteralExpr(circuit.in_size + i)),
                        IdentifierExpr(cfg.zk_out_name),
                        IdentifierExpr(f'{cfg.zk_out_name}start_idx').binop('+', NumberLiteralExpr(circuit.out_size + o))]
            i, o, p = i + cgens[fdef].in_size_trans, o + cgens[fdef].out_size_trans, p + cgens[fdef].priv_in_size_trans
        assert i == circuit.trans_in_size and o == circuit.trans_out_size and p == circuit.trans_priv_size

    for fct, circ in cgens.items():
        if not fct.requires_verification:
            circ.trans_out_size, circ.trans_in_size, circ.trans_priv_size = 0, 0, 0


def _compute_transitive_circuit_io_sizes(cgens: Dict[ConstructorOrFunctionDefinition, CircuitHelper], fct, gkeys):
    gkeys.update(cgens[fct].requested_global_keys)
    circuit = cgens[fct]

    if circuit.trans_in_size is not None:
        return circuit.trans_in_size, circuit.trans_out_size, circuit.trans_priv_size
    elif not circuit.function_calls_with_verification:
        return 0, 0, 0
    else:
        insum, outsum, psum = 0, 0, 0
        for f in circuit.function_calls_with_verification:
            i, o, p = _compute_transitive_circuit_io_sizes(cgens, f.func.target, gkeys)
            target_circuit = cgens[f.func.target]
            insum += i + target_circuit.in_size
            outsum += o + target_circuit.out_size
            psum += p + target_circuit.priv_in_size
        return insum, outsum, psum
