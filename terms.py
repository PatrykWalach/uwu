import dataclasses
import typing 
A = typing.TypeVar('A')
B = typing.TypeVar('B')
C = typing.TypeVar('C')
D = typing.TypeVar('D')
E = typing.TypeVar('E')
F = typing.TypeVar('F')
G = typing.TypeVar('G')
H = typing.TypeVar('H')
I = typing.TypeVar('I')
J = typing.TypeVar('J')
K = typing.TypeVar('K')
L = typing.TypeVar('L')
M = typing.TypeVar('M')
R = typing.TypeVar('R')

@dataclasses.dataclass(frozen=True)
class VariableDeclaration(typing.Generic[C, D]):
    id: C
    init: D


@dataclasses.dataclass(frozen=True)
class Do(typing.Generic[A]):
    body: list[A]


@dataclasses.dataclass(frozen=True)
class Program(typing.Generic[B]):
    body: list[B]


@dataclasses.dataclass(frozen=True)
class BinaryExpr(typing.Generic[E,F]):
    op: typing.Literal['++','+','-','/','*','//']
    left: E
    right:F


@dataclasses.dataclass(frozen=True)
class Identifier:
    name: str

@dataclasses.dataclass(frozen=True)
class Literal:
    raw: str
    value: float | str


AstNode: typing.TypeAlias = Program[R]| Do[R]|VariableDeclaration[R,R]|Identifier|BinaryExpr[R,R]
AstTree: typing.TypeAlias = AstNode['AstTree']
