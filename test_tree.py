import sys
from unittest import TestCase
from random import randint
from tree import BinaryTree


def gen_test_arr(n):
    return [randint(0, n + 1)] * n


def base_test(n, strategy='thunk'):
    array = gen_test_arr(n)
    tree = BinaryTree()

    for i in array:
        tree.insert(i)

    return sorted(array), tree.traverse(strategy=strategy)


class TestBinaryTree(TestCase):
    """
    Since we made a binary tree, a simple way to check if
    the traversal works is to check if the resulting array
    is ordered.

    Of course, this implies that the insertion operation works,
    but since it's a pretty straight forward binary tree without
    balancing, I'm not too worried about that.

    Also, since only the thunk version is the only one that is
    "tail optimized" since python doesn't have tail call optimization,
    the only one we can test with a big array that would overflow a
    callstack is _traverse_apply_thunk
    """

    def test__traverse_naive(self):
        self.assertEqual(*base_test(100, 'naive'))

    def test__traverse_cps(self):
        self.assertEqual(*base_test(100, 'cps'))

    def test__traverse_explicit(self):
        self.assertEqual(*base_test(100, 'explicit'))

    def test__traverse_apply(self):
        self.assertEqual(*base_test(100, 'apply'))

    def test__traverse_apply_thunk(self):
        self.assertEqual(*base_test(100, 'thunk'))

    def test__traverse_apply_thunk_massive(self):
        self.assertEqual(*base_test(10000, 'thunk'))
