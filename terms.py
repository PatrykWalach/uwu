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
class EVariableDeclaration:
    id: EIdentifier
    init: Expr
    hint: EHint | None = None


@dataclasses.dataclass(frozen=True)
class EDo:
    body: list[Expr]
    hint: EHint | None = None


@dataclasses.dataclass(frozen=True)
class EProgram:
    body: list[Expr | EEnumDeclaration]


@dataclasses.dataclass(frozen=True)
class EBinaryExpr:
    op: typing.Literal["++", "+", "-", "/", "*", "//", '>', '<', '<=', '>=']
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
    hint: EHint | None = None


@dataclasses.dataclass(frozen=True)
class EParam:
    identifier: EIdentifier
    hint: EHint | None = None
@dataclasses.dataclass(frozen=True)
class EParamPattern:
    identifier: EIdentifier


@dataclasses.dataclass(frozen=True)
class ECaseOf:
    of: Expr
    cases: list[ECase]


@dataclasses.dataclass(frozen=True)
class ECase:
    pattern: EEnumPattern | EParamPattern
    body: EDo


@dataclasses.dataclass(frozen=True)
class EEnumPattern:
    id: EIdentifier
    patterns: list[EEnumPattern | EParamPattern]


@dataclasses.dataclass(frozen=True)
class ECall:
    callee: EIdentifier
    arguments: list[Expr]


@dataclasses.dataclass(frozen=True)
class EIf:
    test: Expr
    then: EBlockStmt
    or_else: EBlockStmt | EIf | None
    hint: EHint | None = None


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
    | EIf
    | EBlockStmt
    | EEnumDeclaration
    | EEnumPattern
    | EFieldsUnnamed
    | EHint
    | EVariant |EParamPattern

)
AstTree: typing.TypeAlias = AstNode

Expr: typing.TypeAlias = EDo | ELiteral | EDef | EIf | ECall | ECaseOf | EVariableDeclaration | EIdentifier | EBinaryExpr

# 'type_identifier',  "array", "tuple",
