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
class EParamPattern:
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
    callee: EIdentifier
    arguments: list[Expr]


@dataclasses.dataclass(frozen=True)
class EArray:
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
class EArrayPattern:
    first: list[Pattern]
    rest: ESpread | None


@dataclasses.dataclass(frozen=True)
class ESpread:
    rest: EIdentifier
    last: list[Pattern]
    #


@dataclasses.dataclass(frozen=True)
class EFieldsUnnamed:
    unnamed: list[EIdentifier]


AstNode: typing.TypeAlias = (
    EProgram
    | EDo
    | EVariableDeclaration
    | EIdentifier
    | EBinaryExpr
    | ELiteral
    | EDef
    | EParam
    | ECaseOf
    | ECase
    | ECall
    | EArray
    | EIf
    | EBlockStmt
    | EEnumDeclaration
    | EEnumPattern
    | EFieldsUnnamed
    | EHint
    | EVariant
    | EParamPattern
    | EArrayPattern
    | ESpread
    | EHintNone
    | EIfNone
)


AstTree: typing.TypeAlias = AstNode
Pattern: typing.TypeAlias = EParamPattern | EArrayPattern | EEnumPattern
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
)

# 'type_identifier',  "array", "tuple",
