import typing
import typed
import dataclasses
import terms

A = typing.TypeVar("A")
B = typing.TypeVar("B")
C = typing.TypeVar("C")
D = typing.TypeVar("D")
E = typing.TypeVar("E")
F = typing.TypeVar("F")
G = typing.TypeVar("G")
H = typing.TypeVar("H")
I = typing.TypeVar("I")
J = typing.TypeVar("J")
K = typing.TypeVar("K")
L = typing.TypeVar("L")
M = typing.TypeVar("M")
R = typing.TypeVar("R")


@dataclasses.dataclass(frozen=True)
class Typed(typing.Generic[A]):
    ty: typed.Type
    node: terms.AstNode[A]


TypedAstNode: typing.TypeAlias = Typed[R]
TypedAstTree: typing.TypeAlias = TypedAstNode["TypedAstTree"]




# class Scheme:
#     type: Type
#     bound :list[int]