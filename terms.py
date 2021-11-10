import dataclasses
import typing
import typed

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
N = typing.TypeVar("N")
O = typing.TypeVar("O")
P = typing.TypeVar("P")
R = typing.TypeVar("R")
S = typing.TypeVar("S")
T = typing.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class VariableDeclaration(typing.Generic[C, D]):
    id: C
    init: D
    hint: typed.Type | None = None


@dataclasses.dataclass(frozen=True)
class Do(typing.Generic[A]):
    body: list[A]
    hint: typed.Type | None = None


@dataclasses.dataclass(frozen=True)
class Program(typing.Generic[B]):
    body: list[B]


@dataclasses.dataclass(frozen=True)
class BinaryExpr(typing.Generic[E, F]):
    op: typing.Literal["++", "+", "-", "/", "*", "//"]
    left: E
    right: F


@dataclasses.dataclass(frozen=True)
class Identifier:
    name: str


@dataclasses.dataclass(frozen=True)
class Literal:
    raw: str
    value: float | str


@dataclasses.dataclass(frozen=True)
class Def(typing.Generic[G, H, I]):
    identifier: G
    params: list[H]
    body: I
    hint: typing.Type | None = None


@dataclasses.dataclass(frozen=True)
class Param(typing.Generic[J]):
    identifier: J
    hint: typing.Type | None = None


@dataclasses.dataclass(frozen=True)
class CaseOf(typing.Generic[K, L]):
    of: K
    cases: list[L]


@dataclasses.dataclass(frozen=True)
class Case(typing.Generic[M, N]):
    pattern: M
    body: N


@dataclasses.dataclass(frozen=True)
class EnumPattern(typing.Generic[O, P]):
    id: O
    patterns: P


@dataclasses.dataclass(frozen=True)
class Call(typing.Generic[R, S]):
    callee: R
    arguments: list[S]


AstNode: typing.TypeAlias = (
    Program[R]
    | Do[R]
    | VariableDeclaration[R, R]
    | Identifier
    | BinaryExpr[R, R]
    | Literal
    | Def[R, R, R]
    | Param[R]
    | CaseOf[R, R]
    | Case[R, R]
    | Call[R, R]
)
AstTree: typing.TypeAlias = AstNode["AstTree"]
