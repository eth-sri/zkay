from __future__ import annotations
from typing import Set, Dict, Optional


class PartitionState:
    """
    Supports operations on partitions

    * insert: create a new partition with a single element
    * merge: merge partitions
    * ...
    """

    def __init__(self):
        self._partitions: Dict[int, Set[object]] = {}
        self._next_unused = 0

    def insert(self, x):
        p = {x}
        self._insert_partition(p)

    def _insert_partition(self, p):
        self._partitions[self._next_unused] = p
        self._next_unused += 1

    def get_index(self, x) -> Optional[int]:
        """
        Return index for element x.

        :param x:
        :return: the index of the partition containing x
        """
        for k, p in self._partitions.items():
            if x in p:
                return k
        return None

    def has(self, x) -> bool:
        return self.get_index(x) is not None

    def same_partition(self, x, y) -> bool:
        if x == y:
            return True

        # get x
        xp = self.get_index(x)
        if xp is None:
            return False
        # get y
        yp = self.get_index(y)
        if yp is None:
            return False
        # compare
        return xp == yp

    def merge(self, x, y):
        # locate
        xp_key = self.get_index(x)
        yp_key = self.get_index(y)

        if xp_key == yp_key:
            # merging not necessary
            return

        # remove y
        yp = self._partitions.pop(yp_key)

        # insert y
        self._partitions[xp_key].update(yp)

    def remove(self, x):
        """
        Removes x from its partition

        :param x:
        :return:
        """

        # locate
        xp_key = self.get_index(x)
        assert xp_key is not None, f'element {x} not found'

        # remove x
        self._partitions[xp_key].remove(x)

        # potentially remove whole partition
        if len(self._partitions[xp_key]) == 0:
            del self._partitions[xp_key]

    def move_to(self, x, y):
        """
        Moves x to the partition of y

        :param x:
        :param y:
        """
        if self.same_partition(x, y):
            # no action necessary
            return

        # remove
        self.remove(x)

        # locate y
        yp_key = self.get_index(y)

        # insert x
        self._partitions[yp_key].add(x)

    def move_to_separate(self, x):
        """
        Moves x to a fresh partition

        :param x:
        """

        # remove
        self.remove(x)

        # insert
        self.insert(x)

    def separate_all(self) -> PartitionState:
        s = PartitionState()
        for p in self._partitions.values():
            # Side effects do not affect the aliasing of final values
            final_vals = set()
            for x in p:
                if x.is_final:
                    final_vals.add(x)
                else:
                    s.insert(x)
            if final_vals:
                s._insert_partition(final_vals)
        return s

    def join(self, other: PartitionState) -> PartitionState:
        """
        Combine two states.
        Overlaps in partitions between self and other will be preserved.
        e.g. if self contains (a, b, c), (x) and other contains (a, b), (c, x), new state will contain (a, b), (c), (x)

        :param other: other state, must contain the same values as self (partitions can be different)
        :return: joined state
        """
        s = PartitionState()

        # Collect all values
        my_vals = frozenset([item for subset in self._partitions.values() for item in subset])
        other_vals = frozenset([item for subset in other._partitions.values() for item in subset])
        assert not my_vals.symmetric_difference(other_vals), 'joined branches do not contain the same values'
        values_in_both = my_vals.intersection(other_vals)

        new_parts = set()
        for val in values_in_both:
            my_part = self._partitions[self.get_index(val)]
            other_part = other._partitions[other.get_index(val)]

            shared_elems = my_part.intersection(other_part)
            new_parts.add(frozenset(shared_elems))

        for part in new_parts:
            s._insert_partition(set(part))
        return s

    def copy(self, project=None):
        """
        Create a shallow copy of the partition state.

        :param project: (iterator) if not None, only keep entries that are in project
        :return:
        """
        c = PartitionState()
        c._next_unused = self._next_unused
        for k, p in self._partitions.items():
            # shallow copy
            kept = {x for x in p if project is None or x in project}
            if len(kept) > 0:
                c._partitions[k] = kept
        return c

    def __str__(self):

        ps = [sorted({str(e) for e in p}) for k, p in self._partitions.items()]
        ps.sort()
        return str(ps)
