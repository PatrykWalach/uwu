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
class ELet:
    id: str
    init: Expr
    hint: EHint | EHintNone = EHintNone()


@dataclasses.dataclass(frozen=True)
class EDo:
    body: list[Stmt] = dataclasses.field(default_factory=list)
    hint: EHint | EHintNone = EHintNone()


@dataclasses.dataclass(frozen=True)
class EProgram:
    body: list[Stmt] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EBinaryExpr:
    op: typing.Literal["++", "+", "-", "/", "*", "%", "//", ">", "<", "|", "!=", "=="]
    left: Expr
    right: Expr


@dataclasses.dataclass(frozen=True)
class EIdentifier:
    name: str


@dataclasses.dataclass(frozen=True)
class ELiteral:
    value: float | str


@dataclasses.dataclass(frozen=True)
class EExternal:
    value: str


@dataclasses.dataclass(frozen=True)
class EDef:
    identifier: str
    params: list[EParam]
    body: EDo
    hint: EHint | EHintNone = EHintNone()
    generics: list[EIdentifier] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EParam:
    identifier: str
    hint: EHint | EHintNone = EHintNone()


@dataclasses.dataclass(frozen=True)
class EUnaryExpr:
    op: typing.Literal["-"]
    expr: Expr


@dataclasses.dataclass(frozen=True)
class EMatchAs:
    identifier: str


@dataclasses.dataclass(frozen=True)
class ECaseOf:
    expr: Expr
    cases: list[ECase] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class ECase:
    pattern: Pattern
    body: EDo = dataclasses.field(default_factory=EDo)


@dataclasses.dataclass(frozen=True)
class EMatchVariant:
    id: str
    patterns: list[Pattern] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class ECall:
    callee: Expr
    args: list[Expr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EVariantCall:
    callee: str
    args: list[Expr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EArray:
    args: list[Expr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class ETuple:
    args: list[Expr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EIfNone:
    pass


@dataclasses.dataclass(frozen=True)
class EIf:
    test: Expr
    then: EBlock
    or_else: EBlock | EIf | EIfNone = EIfNone()
    hint: EHint | EHintNone = EHintNone()

    @staticmethod
    def from_option(hint: None | EHint):
        if hint == None:
            return EIfNone()
        return hint


@dataclasses.dataclass(frozen=True)
class EBlock:
    body: list[Stmt] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EHint:
    id: str
    args: list[Type] = dataclasses.field(default_factory=list)

    @staticmethod
    def from_option(hint):
        if hint == None:
            return EHintNone()
        return hint


@dataclasses.dataclass(frozen=True)
class EEnumDeclaration:
    id: str
    variants: list[EVariant] = dataclasses.field(default_factory=list)
    generics: list[EIdentifier] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EVariant:
    id: str
    fields: list[EHint] = dataclasses.field(default_factory=list)


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


Pattern: typing.TypeAlias = EMatchAs | EMatchVariant

Expr: typing.TypeAlias = (
    ELiteral
    | EIf
    | ECall
    | ECaseOf
    | EIdentifier
    | EBinaryExpr
    | EArray
    | ETuple
    | EVariantCall
    | EExternal
    | EUnaryExpr
)

# 'type_identifier',  "array", "tuple",
Type: typing.TypeAlias = EHint | EHintNone

Stmt: typing.TypeAlias = Expr | ELet | EEnumDeclaration | EDef

AstTree: typing.TypeAlias = (
    EProgram
    | EParam
    | ECaseOf
    | ECase
    | EBlock
    | EFieldsUnnamed
    | Type
    | EVariant
    | EIfNone
    | Pattern
    | Stmt
)
