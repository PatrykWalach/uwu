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
class TypedLiteral(terms.Literal):
    type: typed.Type


@dataclasses.dataclass(frozen=True)
class TypedProgram(terms.Program[A]):
    type: typed.Type


@dataclasses.dataclass(frozen=True)
class TypedDo(terms.Do[B]):
    type: typed.Type


@dataclasses.dataclass(frozen=True)
class TypedVariableDeclaration(terms.VariableDeclaration[C, D]):
    type: typed.Type

@dataclasses.dataclass(frozen=True)
class TypedBinaryExpr(terms.BinaryExpr[E, F]):
    type: typed.Type


@dataclasses.dataclass(frozen=True)
class TypedIdentifier(terms.Identifier):
    type: typed.Type


TypedAstNode: typing.TypeAlias = (
    TypedProgram[R]
    | TypedDo[R]
    | TypedVariableDeclaration[R, R]
    | TypedIdentifier
    | TypedLiteral|TypedBinaryExpr[R,R]
)
TypedAstTree: typing.TypeAlias = TypedAstNode["TypedAstTree"]
