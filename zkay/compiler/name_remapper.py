from __future__ import annotations

from contextlib import contextmanager
from typing import Generic, TypeVar, Dict, ContextManager, Any, Callable

from zkay.zkay_ast.ast import Expression, IdentifierExpr, HybridArgumentIdf

K = TypeVar('K')
V = TypeVar('V')
class Remapper(Generic[K, V]):
    """
    Helper class to simulate static single assignment, mostly used by CircuitHelper
    For a given name it keeps track which value the name currently refers to (e.g. current SSA identifier)

    e.g. if we have
    x = 1
    x = 2
    x = x + 1

    we can then simulate ssa by using the remapper whenever an identifier is read or written:
    tmp1 = 1
    remap(x, tmp1)
    tmp2 = 2
    remap(x, tmp2)
    tmp3 = get_current(x) + 1
    remap(x, tmp3)

    :param K: name type
    :param V: type of element to which key refers at a code location
    """

    RemapMapType = Dict #[(bool, K), V]

    def __init__(self) -> None:
        super().__init__()
        self.rmap = {}

    def __bool__(self):
        """
        Check if any name is currently remapped.

        :return: True if there exists at least one key which is currently remapped to a different value
        """
        return bool(self.rmap)

    def clear(self):
        self.rmap.clear()

    def remap(self, key: K, is_local: bool, value: V):
        """
        Remap key to refer to new version element 'value'.

        :param key: The key/identifier to update
        :param is_local: Remappings for local keys will be discarded once the current remap scope is left
        :param value: latest version of the element to which key refers
        """
        self.rmap[(is_local, key)] = value

    @contextmanager
    def remap_scope(self, persist_globals: bool) -> ContextManager:
        """
        Return a context manager which will automatically rollback the remap state once the end of the with statement is reached.

        :param persist_globals: If True, keys with is_local=False will not be removed upon rollback
        :return: context manager
        """
        prev = self.rmap.copy()
        yield
        if persist_globals:
            prev.update({(is_loc, key): val for (is_loc, key), val in self.rmap.items() if not is_loc})
        self.rmap = prev

    def is_remapped(self, key: K, is_local=True) -> bool:
        return (is_local, key) in self.rmap

    def get_current(self, key: K, is_local=True, default=None) -> V:
        """
        Return the value to which key currently refers.

        :param key: Name to lookup
        :param is_local: Is it a local name?
        :param default: If set, this will be returned if key is not currently remapped

        :except KeyError: raised if key not currently mapped and default=None
        :return: The current value
        """
        k = (is_local, key)
        if k in self.rmap:
            return self.rmap[k]
        else:
            if default is None:
                raise KeyError()
            return default

    def get_state(self) -> Any:
        """ Return an opaque copy of the internal state. """
        return self.rmap.copy()

    def set_state(self, state: Any):
        """ Restore internal state from an opaque copy previously obtained using get_state. """
        assert isinstance(state, Dict)
        self.rmap = state

    def join_branch(self, true_cond_for_other_branch: IdentifierExpr, other_branch_state: Any, create_val_for_name_and_cond_fct: Callable[[K, Expression], V]):
        """
        Perform an SSA join for two branches.

        i.e. if key is not remapped in any branch -> keep previous remapping
             if key is altered in at least one branch -> remap to conditional assignment of latest remapped version in either branch

        example usage:
            with remapper.remap_scope(persist_globals=False):
                <process true branch>
                true_state = remapper.get_state()
            if <has false branch>:
                <process false branch>
            remapper.join_branch(cond_idf_expr, true_state, <create_tmp_var(idf, expr) function>)

        :param true_cond_for_other_branch: IdentifierExpression which evaluates to true at runtime if other_branch is taken
        :param other_branch_state: remap state at the end of other branch (obtained using get_state)
        :param create_val_for_name_and_cond_fct: function to introduce a new temporary variable to which the given expression is assigned
        """
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
    """Remapper class used by CircuitHelper"""
    pass
