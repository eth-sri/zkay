from __future__ import annotations

from contextlib import contextmanager
from typing import Generic, TypeVar, Dict, ContextManager, Any, Callable

from zkay.zkay_ast.ast import Expression, IdentifierExpr, HybridArgumentIdf

K = TypeVar('K')
V = TypeVar('V')
class Remapper(Generic[K, V]):
    RemapMapType = Dict #[(bool, K), V]

    def __init__(self) -> None:
        super().__init__()
        self.rmap = {}

    def __bool__(self):
        return bool(self.rmap)

    def clear(self):
        self.rmap.clear()

    def remap(self, key: K, is_local: bool, value: V):
        self.rmap[(is_local, key)] = value

    @contextmanager
    def remap_scope(self, persist_globals: bool) -> ContextManager:
        prev = self.rmap.copy()
        yield
        if persist_globals:
            prev.update({(is_loc, key): val for (is_loc, key), val in self.rmap.items() if not is_loc})
        self.rmap = prev

    def get_current(self, key: K, is_local=True, default=None) -> V:
        k = (is_local, key)
        if k in self.rmap:
            return self.rmap[k]
        else:
            if default is None:
                raise KeyError()
            return default

    def get_state(self) -> Any:
        return self.rmap.copy()

    def set_state(self, state: Any):
        assert isinstance(state, Dict)
        self.rmap = state

    def join_branch(self, true_cond_for_other_branch: IdentifierExpr, other_branch_state: Any, create_val_for_name_and_cond_fct: Callable[[K, Expression], V]):
        true_state = other_branch_state
        false_state = self.rmap
        self.rmap = {}
        for key, val in true_state.items():
            if key not in false_state or false_state[key].name == val.name:
                # no conflict
                self.rmap[key] = val
            else:
                # conflict -> assign conditional assignment result to new version of variable
                then_idf = true_state[key]
                else_idf = false_state[key]
                rhs = true_cond_for_other_branch.clone().ite(IdentifierExpr(then_idf).as_type(then_idf.t),
                                                     IdentifierExpr(else_idf).as_type(else_idf.t)).as_type(then_idf.t)
                self.rmap[key] = create_val_for_name_and_cond_fct(key[1], rhs)


class CircVarRemapper(Remapper[str, HybridArgumentIdf]):
    pass
