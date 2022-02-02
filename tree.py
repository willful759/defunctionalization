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


class Thunk:
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.fn(*self.args, **self.kwargs)


@dataclass
class LeftInsert:
    right: Union[None | Leaf | Node]
    value: Any
    cont: Union['LeftInsert', 'RightInsert', 'DoneInsert']


@dataclass
class RightInsert:
    left: Union[None | Leaf | Node]
    value: Any
    cont: Union['LeftInsert', 'RightInsert', 'DoneInsert']


@dataclass
class DoneInsert:
    pass


@dataclass
class BinaryTree:
    head: Leaf | Node = None

    @staticmethod
    def _handle_leaf(root, value, insert_left):
        match root:
            case None:
                return Leaf(value)
            case Leaf(val):
                if insert_left:
                    return Node(Leaf(value), val, None)
                else:
                    return Node(None, val, Leaf(value))

    # if this looks suspicious, yes I did defunctionalize `insert`
    def insert(self, value):
        if self.head is None:
            self.head = Leaf(value)
            return

        elif isinstance(self.head, Leaf):
            if value < self.head.value:
                self.head = Node(Leaf(value), self.head.value, None)
            else:
                self.head = Node(None, self.head.value, Leaf(value))
            return

        root = self.head
        while root is not None:
            if value < root.value:
                if isinstance(root.left, Node):
                    root = root.left
                else:
                    root.left = BinaryTree._handle_leaf(
                        root.left, value, True
                    )
                    return
            else:
                if isinstance(root.right, Node):
                    root = root.right
                else:
                    root.right = BinaryTree._handle_leaf(
                        root.right, value, False
                    )
                    return

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

    @staticmethod
    def _trampoline(thunk):
        # since python doesn't have tail call optimization
        # we need to implement our own
        while isinstance(thunk, Thunk):
            thunk = thunk()
        return thunk

    @staticmethod
    def _apply_thunk(cont: Done | Next | Concat, value):
        match cont:
            case Done():
                return value

            case Next(right, val, fn, cont):
                return Thunk(BinaryTree._traverse_apply_thunk,
                             right, fn,
                             Concat(value, val, fn, cont)
                             )

            case Concat(ls, val, fn, cont):
                return Thunk(BinaryTree._apply_thunk,
                             cont, ls + [fn(val)] + value
                             )

    @staticmethod
    def _traverse_apply_thunk(root, fn, cont):
        match root:
            case None:
                return Thunk(BinaryTree._apply_thunk, cont, [])

            case Leaf(value):
                return Thunk(BinaryTree._apply_thunk, cont, [fn(value)])

            case Node(left, value, right):
                return Thunk(
                    BinaryTree._traverse_apply_thunk, left, fn,
                    Next(right, value, fn, cont)
                )

    def traverse(self, fn: Callable = lambda x: x, strategy: str = 'thunk'):
        match strategy:
            case 'apply':
                return BinaryTree._traverse_apply(self.head, fn, Done())
            case 'explicit':
                return BinaryTree._traverse_explicit(
                    self.head, fn, BinaryTree._done
                )
            case 'cps':
                return BinaryTree._traverse_cps(self.head, fn, lambda x: x)
            case 'naive':
                return BinaryTree._traverse_naive(self.head, fn)
            case 'thunk':
                return BinaryTree._trampoline(
                    BinaryTree._traverse_apply_thunk(self.head, fn, Done())
                )
            case _:
                raise ValueError(f"invalid strategy: {strategy}")
