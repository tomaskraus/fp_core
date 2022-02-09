"""
functional programming basics
"""

from typing import Any, Callable, Iterable
from typing import Protocol


# types ----------

OneArgFunc = Callable[[Any], Any]
TwoArgsFunc = Callable[[Any, Any], Any]
ForkFunc = Callable[[OneArgFunc, OneArgFunc], None]

class Functor(Protocol):
    """
    Functor type
    """
    def map(self, fn: OneArgFunc) -> 'Functor': ...

# ----------------


def none_fn(_: Any) -> None:
    """
    >>> none_fn(2)

    """
    return None


def identity(x: Any) -> Any:
    """
    >>> identity(1)
    1
    """
    return x


def compose(f: OneArgFunc, g: OneArgFunc) -> OneArgFunc:
    """
    >>> compose(lambda x : x+1, lambda x : 2*x)(10)
    21
    """
    return lambda x: f(g(x))


def curry2(fn: TwoArgsFunc) -> Callable[[Any], OneArgFunc]:
    """
    >>> curry2(lambda x, y : x + y)(10)(20)
    30
    """
    return lambda x: lambda y: fn(x, y)


def tap(fn: OneArgFunc) -> OneArgFunc:
    """
    >>> tap(lambda x : x+1)(5)
    5

    >>> tap(lambda x : print(f'oo {x+1} oo'))(5)
    oo 6 oo
    5

    >>> tap(lambda x : None)(5)
    5
    """
    def _tap(x):
        fn(x)
        return x
    return _tap


def curried_map(fn: OneArgFunc) -> Callable[[Iterable[Any]], Iterable[Any]]:
    """
    >>> curried_map(lambda x: x + 1)([1, 2, 3])
    [2, 3, 4]
    """
    return lambda items: list(map(fn, items))


TaskFunc = Callable[[Any], 'Task']


class Task:
    """
    A rewrite of Task to Python from:
        https://github.com/MostlyAdequate/mostly-adequate-guide/blob/master/appendix_b.md
    """

    def __init__(self, fork: ForkFunc):
        self.fork = fork

    @staticmethod
    def rejected(x: Any) -> 'Task':
        """
        failure
        """
        return Task(lambda reject, _: reject(x))

    @staticmethod
    def of(x: Any) -> 'Task':
        """
        pointed
        """
        return Task(lambda _, resolve: resolve(x))

    def map(self, fn: OneArgFunc) -> 'Task':
        """
        functor
        """
        return Task(lambda reject, resolve: self.fork(reject, lambda x: resolve(fn(x))))

    def chain(self, fn: TaskFunc) -> 'Task':
        """
        monad
        """
        return Task(lambda reject, resolve: self.fork(reject,
                                                      lambda x: fn(x).fork(reject, resolve)))

    def ap(self, other_task: 'Task') -> 'Task':
        """
        applicative
        """
        return self.chain(other_task.map)

    def join(self) -> 'Task':
        """
        monad
        """
        return self.chain(identity)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # task of
    t = Task.of(4.5)
    t.fork(none_fn, print)

    # task map
    t.map(lambda x: 2*x).fork(none_fn, print)

    # task chain
    t.chain(lambda a: Task.of(10*a)).fork(none_fn, print)

    # task ap
    addT = Task.of(lambda x: x + 1)
    addT.ap(t).fork(none_fn, print)

    addT2 = Task.of(curry2(lambda a, b: a + b))
    addT2.ap(t).ap(Task.of(100)).fork(none_fn, print)

    # task join
    tt = Task.of(Task.of(2))
    tt.join().fork(none_fn, print)
