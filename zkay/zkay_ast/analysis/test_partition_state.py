from unittest import TestCase

from zkay.zkay_ast.analysis.partition_state import PartitionState


class TestPartitionState(TestCase):

    def test_same_partition(self):
        s = PartitionState()

        for i in range(10):
            s.insert(i)

        self.assertTrue(s.same_partition(0, 0))

        for i in range(1, 10):
            self.assertFalse(s.same_partition(0, i))

    def test_merge(self):
        s = PartitionState()

        for i in range(10):
            s.insert(i)

        for i in range(5):
            s.merge(i, i + 5)

        for i in range(5):
            self.assertTrue(s.same_partition(i, i + 5))

    def test_self_merge(self):
        s = PartitionState()
        s.insert(0)
        s.merge(0, 0)
        self.assertTrue(s.same_partition(0, 0))

    def test_merge_indirect(self):
        s = PartitionState()

        for i in range(10):
            s.insert(i)

        for i in range(9):
            s.merge(i, i + 1)

        for i in range(10):
            self.assertTrue(s.same_partition(0, i))

    def test_remove(self):
        s = PartitionState()

        for i in range(10):
            s.insert(i)

        for i in range(9):
            s.merge(i, i + 1)

        for i in range(5, 10):
            s.remove(i)

        for i in range(5):
            self.assertTrue(s.same_partition(0, i))

    def test_move_to(self):
        s = PartitionState()

        for i in range(10):
            s.insert(i)

        for i in range(5):
            s.merge(0, i)

        for i in range(5, 10):
            s.merge(5, i)

        s.move_to(0, 5)

        for i in range(1, 5):
            self.assertTrue(s.same_partition(1, i))

        for i in range(5, 10):
            self.assertTrue(s.same_partition(0, i))
