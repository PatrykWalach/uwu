from typing import Callable, TypeVar

A =TypeVar('A')
B =TypeVar('B')

def ap(fn:Callable[[A],B], lst:list[A]) -> list[B]:
    return [fn(x) for x in lst]