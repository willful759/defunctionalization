from dataclasses import dataclass
from typing import Any, Union, Callable


@dataclass
class Leaf:
    value: Any


@dataclass
class Node:
    left: Union[None, Leaf, 'Node']
    value: Any
    right: Union[None, Leaf, 'Node']


@dataclass
class Done:
    pass


@dataclass
class Next:
    right: Union[None, Leaf, 'Node']
    val: Any
    fn: Callable
    cont: Union['Done', 'Concat', 'Next']


@dataclass
class Concat:
    ls: Any
    val: Any
    fn: Callable
    cont: Union['Done', 'Concat', 'Next']


@dataclass
class BinaryTree:
    head: Leaf | Node = None

    @staticmethod
    def _insert(root, value):
        match root:
            case None:
                return Leaf(value)

            case Leaf(val):
                if value < val:
                    return Node(Leaf(value), val, None)
                else:
                    return Node(None, val, Leaf(value))

            case Node(left, val, right):
                if value < val:
                    return Node(
                        BinaryTree._insert(left, value),
                        val,
                        right
                    )
                else:
                    return Node(
                        left,
                        val,
                        BinaryTree._insert(right, value)
                    )

    @staticmethod
    def _traverse_naive(root, fn: Callable):
        match root:
            case None:
                return []
            case Leaf(value):
                return [fn(value)]
            case Node(left, value, right):
                return BinaryTree._traverse_naive(left, fn) + \
                       [fn(value)] + \
                       BinaryTree._traverse_naive(right, fn)

    @staticmethod
    def _traverse_cps(root, fn: Callable, cont: Callable):
        match root:
            case None:
                return cont([])

            case Leaf(value):
                return cont([fn(value)])

            case Node(left, value, right):
                return BinaryTree._traverse_cps(
                    left, fn, lambda ls: BinaryTree._traverse_cps(
                        right, fn, lambda rs: cont(
                            ls + [fn(value)] + rs
                        )
                    )
                )

    @staticmethod
    def _done(x):
        return x

    @staticmethod
    def _next(val, right, fn):
        # sadly there's no currying in python
        return lambda ls: BinaryTree._traverse_explicit(
            right, fn, BinaryTree._concat(ls, val, fn))

    @staticmethod
    def _concat(ls, val, fn):
        return lambda rs: ls + [fn(val)] + rs

    @staticmethod
    def _traverse_explicit(root, fn: Callable, cont: Callable):
        match root:
            case None:
                return cont([])

            case Leaf(value):
                return cont([fn(value)])

            case Node(left, value, right):
                print(cont)
                return cont(BinaryTree._traverse_explicit(
                    left, fn,
                    BinaryTree._next(value, right, fn)
                ))

    @staticmethod
    def _apply(cont: Done | Next | Concat, value):
        match cont:
            case Done():
                return value

            case Next(right, val, fn, cont):
                return BinaryTree._traverse_apply(
                    right, fn,
                    Concat(value, val, fn, cont)
                )

            case Concat(ls, val, fn, cont):
                return BinaryTree._apply(
                    cont, ls + [fn(val)] + value)

    @staticmethod
    def _traverse_apply(root, fn, cont):
        match root:
            case None:
                return BinaryTree._apply(cont, [])

            case Leaf(value):
                return BinaryTree._apply(cont, [fn(value)])

            case Node(left, value, right):
                return BinaryTree._traverse_apply(
                    left, fn, Next(right, value, fn, cont))

    def traverse(self, fn: Callable = lambda x: x):
        return BinaryTree._traverse_apply(
            self.head, fn, Done())

    def insert(self, value):
        self.head = BinaryTree._insert(self.head, value)


def main():
    tree = BinaryTree()
    tree.insert(2)
    tree.insert(1)
    tree.insert(0)
    tree.insert(3)
    tree.insert(4)
    print(tree)
    for node in tree.traverse():
        print(node)


if __name__ == "__main__":
    main()
