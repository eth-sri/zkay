from typing import Set, Dict


class PartitionState:
    """
    Supports operations on partitions
    - insert: create a new partition with a single element
    - merge: merge partitions
    - ...
    """

    def __init__(self):
        self._partitions: Dict[int, Set[object]] = {}

    def insert(self, x):
        p = {x}
        self._insert_partition(p)

    def _insert_partition(self, p):
        next_partition = len(self._partitions.keys())
        self._partitions[next_partition] = p

    def get_index(self, x):
        """

        :param x:
        :return: the index of the partition containing x
        """
        for k, p in self._partitions.items():
            if x in p:
                return k
        return None

    def has(self, x):
        return self.get_index(x) is not None

    def same_partition(self, x, y):
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

        # remove x
        self._partitions[xp_key].remove(x)

        # potentially remove whole partition
        if len(self._partitions[xp_key]) == 0:
            del self._partitions[xp_key]

    def move_to(self, x, y):
        """

        :param x:
        :param y:
        Moves x to the partition of y
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

        :param x:
        Moves x to a fresh partition
        """

        # remove
        self.remove(x)

        # insert
        self.insert(x)

    def separate_all(self):
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

    def copy(self, project=None):
        """

        :param project: (iterator) if not None, only keep entries that are in project
        :return:
        """
        c = PartitionState()
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
