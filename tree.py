from dataclasses import dataclass, field
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
    def _done(fn):
        # sadly there's no currying in python
        return lambda x: [fn(x)]

    @staticmethod
    def _next(val, right, fn):
        return lambda ls: BinaryTree._traverse_explicit(
            right, fn, BinaryTree._concat(ls, val, fn))

    @staticmethod
    def _concat(ls, val, fn):
        return lambda rs: ls + [fn(val)] + rs

    @staticmethod
    def _traverse_explicit(root, fn: Callable, cont: Callable):
        match root:
            case None:
                return []

            case Leaf(value):
                return cont([fn(value)])

            case Node(left, value, right):
                return BinaryTree._traverse_explicit(
                    left, fn,
                    BinaryTree._next(value, right, fn)
                )

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
                return []

            case Leaf(value):
                return BinaryTree._apply(cont, [fn(value)])

            case Node(left, value, right):
                return BinaryTree._traverse_apply(
                    left, fn, Next(right, value, fn, cont))

    @staticmethod
    def _traverse_stack(root, fn):
        # This wasn't in the talk, but i think that not doing
        # the stack version that I could come up with
        # by just mimicking the behaviour of the `apply` version
        # would leave my understanding a bit short
        match root:
            case None:
                return []
            case Leaf(value):
                return [fn(value)]

        stack = [(root.value, root.right)]
        root = root.left
        results = []

        while len(stack) > 0:
            # following the execution of _traverse_apply, we see that
            # Next will only be applied until we hit a Leaf
            # Therefore we add to the stack until root is a Leaf

            while not isinstance(root, Leaf) and root.left is not None:
                stack.append((root.value, root.right))
                root = root.left

            # Then we need to apply, which corresponds to pop from the stack

            top = stack.pop()

            match top:

                # Basically a special case of ls + val + []
                case (value, None):
                    results.append(fn(root.value))
                    results.append(fn(value))

                # A shortcut to do Concat when there's no real need to
                # Keep doing "recursion" by adding to the stack
                case (value, Leaf(val)):
                    results.append(fn(root.value))
                    results.append(fn(value))
                    results.append(fn(val))

                # _traverse_apply(right, Concat(ls, value))
                case (value, Node(_)):
                    stack.append((value, root.value))
                    root = top[1]

                # apply Concat
                case (value, ls):
                    results.append(fn(ls))
                    results.append(fn(value))
                    results.append(fn(root.value))

        return results

    def traverse(self, fn: Callable = lambda x: x):
        return BinaryTree._traverse_stack(
            self.head, fn)

    def insert(self, value):
        self.head = BinaryTree._insert(self.head, value)


def main():
    tree = BinaryTree()
    tree.insert(2)
    tree.insert(1)
    tree.insert(3)
    for node in tree.traverse():
        print(node)


if __name__ == "__main__":
    main()


