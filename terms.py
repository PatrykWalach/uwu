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
U = typing.TypeVar("U")
W = typing.TypeVar("W")
X = typing.TypeVar("X")
Y = typing.TypeVar("Y")
Z = typing.TypeVar("Z")


@dataclasses.dataclass(frozen=True)
class EVariableDeclaration(typing.Generic[C, D]):
    id: C
    init: D
    hint: typed.Type | None = None


@dataclasses.dataclass(frozen=True)
class EDo(typing.Generic[A]):
    body: list[A]
    hint: typed.Type | None = None


@dataclasses.dataclass(frozen=True)
class EProgram(typing.Generic[B]):
    body: list[B]


@dataclasses.dataclass(frozen=True)
class EBinaryExpr(typing.Generic[E, F]):
    op: typing.Literal["++", "+", "-", "/", "*", "//"]
    left: E
    right: F


@dataclasses.dataclass(frozen=True)
class EIdentifier:
    name: str


@dataclasses.dataclass(frozen=True)
class ELiteral:
    raw: str
    value: float | str


@dataclasses.dataclass(frozen=True)
class EDef(typing.Generic[G, H, I]):
    identifier: G
    params: list[H]
    body: I
    hint: typing.Type | None = None


@dataclasses.dataclass(frozen=True)
class EParam(typing.Generic[J]):
    identifier: J
    hint: typing.Type | None = None


@dataclasses.dataclass(frozen=True)
class ECaseOf(typing.Generic[K, L]):
    of: K
    cases: list[L]


@dataclasses.dataclass(frozen=True)
class ECase(typing.Generic[M, N]):
    pattern: M
    body: N


@dataclasses.dataclass(frozen=True)
class EEnumPattern(typing.Generic[O, P]):
    id: O
    patterns: P


@dataclasses.dataclass(frozen=True)
class ECall(typing.Generic[R, S]):
    callee: R
    arguments: list[S]


@dataclasses.dataclass(frozen=True)
class EIf(typing.Generic[T, U, W]):
    test: T
    then: U
    or_else: W|None
    hint: typing.Type | None = None


@dataclasses.dataclass(frozen=True)
class EBlockStatement(typing.Generic[X]):
    body: list[X]


AstNode: typing.TypeAlias = (
    EProgram[R]
    | EDo[R]
    | EVariableDeclaration[R, R]
    | EIdentifier
    | EBinaryExpr[R, R]
    | ELiteral
    | EDef[R, R, R]
    | EParam[R]
    | ECaseOf[R, R]
    | ECase[R, R]
    | ECall[R, R]
    | EIf[R, R, R]
    | EBlockStatement[R]
)
AstTree: typing.TypeAlias = AstNode["AstTree"]
