from __future__ import annotations

from contextlib import contextmanager
from typing import Generic, TypeVar, Dict, ContextManager, Any, Callable

from zkay.zkay_ast.ast import Expression, IdentifierExpr, HybridArgumentIdf, Identifier, BuiltinFunction, FunctionCallExpr, HybridArgType
from zkay.zkay_ast.pointers.symbol_table import SymbolTableLinker

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
        """Discard the entire remap state."""
        self.rmap.clear()

    def reset_key(self, key: K):
        """Invalidate remapping information for the given key (is_remapped returns false after this)."""
        del self.rmap[key]

    def remap(self, key: K, value: V):
        """
        Remap key to refer to new version element 'value'.

        :param key: The key/identifier to update
        :param value: latest version of the element to which key refers
        """
        assert key.parent is not None
        self.rmap[key] = value

    @contextmanager
    def remap_scope(self, scope_stmt=None) -> ContextManager:
        """
        Return a context manager which will automatically rollback the remap state once the end of the with statement is reached.

        :param scope_stmt: [OPTIONAL] last statement before the scope is entered. If this is not None, remappings for variables which were
                                      already in scope at scope_stmt will not be reset during rollback
        :return: context manager
        """
        prev = self.rmap.copy()
        yield
        if scope_stmt:
            prev.update({key: val for key, val in self.rmap.items() if SymbolTableLinker.in_scope_at(key, scope_stmt)})
        self.rmap = prev

    def is_remapped(self, key: K) -> bool:
        return key in self.rmap

    def get_current(self, key: K, default=None) -> V:
        """
        Return the value to which key currently refers.

        :param key: Name to lookup
        :param default: If set, this will be returned if key is not currently remapped

        :except KeyError: raised if key not currently mapped and default=None
        :return: The current value
        """
        k = key
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
        self.rmap = state.copy()

    def join_branch(self, stmt, true_cond_for_other_branch: IdentifierExpr,
                    other_branch_state: Any, create_val_for_name_and_expr_fct: Callable[[K, Expression], V]):
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

        :param stmt: the branch statement, variables which are not already in scope at that statement are not included in the joined state
        :param true_cond_for_other_branch: IdentifierExpression which evaluates to true at runtime if other_branch is taken
        :param other_branch_state: remap state at the end of other branch (obtained using get_state)
        :param create_val_for_name_and_expr_fct: function to introduce a new temporary variable to which the given expression is assigned
        """
        true_state = other_branch_state
        false_state = self.rmap
        self.rmap = {}

        def join(then_idf, else_idf):
            """Return new temporary HybridArgumentIdf with value cond ? then_idf : else_idf."""
            rhs = FunctionCallExpr(BuiltinFunction('ite'), [true_cond_for_other_branch.clone(), then_idf, else_idf]).as_type(val.t)
            return create_val_for_name_and_expr_fct(key.name, rhs)

        for key, val in true_state.items():
            if not SymbolTableLinker.in_scope_at(key, stmt):
                # Don't keep local values
                continue

            if key in false_state and false_state[key].name == val.name:
                # key was not modified in either branch -> simply keep
                assert false_state[key] == val
                self.rmap[key] = val
            elif key not in false_state:
                # If value was only read (remapping points to a circuit input) -> can just take as-is,
                # otherwise have to use conditional assignment
                if isinstance(val, HybridArgumentIdf) and (val.arg_type == HybridArgType.PUB_CIRCUIT_ARG or val.arg_type == HybridArgType.PRIV_CIRCUIT_VAL):
                    self.rmap[key] = val
                else:
                    # key was only modified in true branch
                    # remap key -> new temporary with value cond ? new_value : old_value
                    assert key.parent.annotated_type.declared_type is not None
                    prev_val = IdentifierExpr(key.clone()).as_type(key.parent.annotated_type.declared_type.clone())
                    prev_val = prev_val.override(target=key.parent, parent=stmt, statement=stmt)
                    self.rmap[key] = join(true_state[key].get_loc_expr(stmt), prev_val)
            else:
                # key was modified in both branches
                # remap key -> new temporary with value cond ? true_val : false_val
                self.rmap[key] = join(true_state[key].get_loc_expr(stmt), false_state[key].get_loc_expr(stmt))
        for key, val in false_state.items():
            if not SymbolTableLinker.in_scope_at(key, stmt):
                # Don't keep local values
                continue

            if key not in true_state:
                if isinstance(val, HybridArgumentIdf) and (val.arg_type == HybridArgType.PUB_CIRCUIT_ARG or val.arg_type == HybridArgType.PRIV_CIRCUIT_VAL):
                    self.rmap[key] = val
                else:
                    # key was only modified in false branch
                    # remap key -> new temporary with value cond ? old_value : new_value
                    assert key.parent.annotated_type.declared_type is not None
                    prev_val = IdentifierExpr(key.clone()).as_type(key.parent.annotated_type.declared_type.clone())
                    prev_val = prev_val.override(target=key.parent, parent=stmt, statement=stmt)
                    self.rmap[key] = join(prev_val, false_state[key].get_loc_expr(stmt))


class CircVarRemapper(Remapper[Identifier, HybridArgumentIdf]):
    """Remapper class used by CircuitHelper"""
    pass
