from __future__ import annotations
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
class EHintNone:
    pass


@dataclasses.dataclass(frozen=True)
class EVariableDeclaration:
    id: EIdentifier
    init: Expr
    hint: EHint | EHintNone = EHintNone()


@dataclasses.dataclass(frozen=True)
class EDo:
    body: list[Expr]
    hint: EHint | EHintNone = EHintNone()


@dataclasses.dataclass(frozen=True)
class EProgram:
    body: list[Expr | EEnumDeclaration]


@dataclasses.dataclass(frozen=True)
class EBinaryExpr:
    op: typing.Literal["++", "+", "-", "/", "*", "//", ">", "<", "<=", ">="]
    left: Expr
    right: Expr


@dataclasses.dataclass(frozen=True)
class EIdentifier:
    name: str


@dataclasses.dataclass(frozen=True)
class ELiteral:
    raw: str
    value: float | str


@dataclasses.dataclass(frozen=True)
class EDef:
    identifier: EIdentifier
    params: list[EParam]
    body: EDo
    hint: EHint | EHintNone = EHintNone()


@dataclasses.dataclass(frozen=True)
class EParam:
    identifier: EIdentifier
    hint: EHint | EHintNone = EHintNone()


@dataclasses.dataclass(frozen=True)
class EMatchAs:
    identifier: EIdentifier


@dataclasses.dataclass(frozen=True)
class ECaseOf:
    of: Expr
    cases: list[ECase]


@dataclasses.dataclass(frozen=True)
class ECase:
    pattern: Pattern
    body: EDo


@dataclasses.dataclass(frozen=True)
class EEnumPattern:
    id: EIdentifier
    patterns: list[Pattern]


@dataclasses.dataclass(frozen=True)
class ECall:
    callee: Expr
    arguments: list[Expr]


@dataclasses.dataclass(frozen=True)
class EArray:
    arguments: list[Expr]


@dataclasses.dataclass(frozen=True)
class ETuple:
    arguments: list[Expr]


@dataclasses.dataclass(frozen=True)
class EIfNone:
    pass


@dataclasses.dataclass(frozen=True)
class EIf:
    test: Expr
    then: EBlockStmt
    or_else: EBlockStmt | EIf | EIfNone = EIfNone()
    hint: EHint | EHintNone = EHintNone()

    @staticmethod
    def from_option(hint):
        if hint == None:
            return EIfNone()
        return hint


@dataclasses.dataclass(frozen=True)
class EBlockStmt:
    body: list[Expr]


@dataclasses.dataclass(frozen=True)
class EHint:
    id: EIdentifier
    arguments: list[EHint]

    @staticmethod
    def from_option(hint):
        if hint == None:
            return EHintNone()
        return hint


@dataclasses.dataclass(frozen=True)
class EEnumDeclaration:
    id: EIdentifier
    generics: list[EIdentifier]
    variants: list[EVariant]


@dataclasses.dataclass(frozen=True)
class EVariant:
    id: EIdentifier
    fields: EFieldsUnnamed


@dataclasses.dataclass(frozen=True)
class EMatchArray:
    patterns: list[Pattern]
    rest: EIdentifier | None = None


@dataclasses.dataclass(frozen=True)
class EMatchTuple:
    patterns: list[Pattern]
    rest: EIdentifier | None = None



@dataclasses.dataclass(frozen=True)
class EFieldsUnnamed:
    unnamed: list[EIdentifier]


Pattern: typing.TypeAlias = (
    EMatchAs | EMatchArray | EEnumPattern | EMatchTuple
)
Expr: typing.TypeAlias = (
    EDo
    | ELiteral
    | EDef
    | EIf
    | ECall
    | ECaseOf
    | EVariableDeclaration
    | EIdentifier
    | EBinaryExpr
    | EArray
    | ETuple
)

# 'type_identifier',  "array", "tuple",

AstTree: typing.TypeAlias = (
    EProgram
    | EParam
    | ECaseOf
    | ECase
    | EBlockStmt
    | EEnumDeclaration
    | EFieldsUnnamed
    | EHint
    | EVariant
    | EHintNone
    | EIfNone
    | Expr
    | Pattern
)
