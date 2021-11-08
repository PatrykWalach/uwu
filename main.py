from __future__ import annotations

from sly import Parser, Lexer
import functools
import json
import operator
import random
from functools import partial, reduce, wraps
from itertools import product
from typing import Any, Callable, Generic, TypeAlias, TypeVar, Union

import dataclasses

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')
E = TypeVar('E')
F = TypeVar('F')
G = TypeVar('G')
H = TypeVar('H')
I = TypeVar('I')
J = TypeVar('J')
K = TypeVar('K')
L = TypeVar('L')
M = TypeVar('M')
R = TypeVar('R')

class UwuLexer(Lexer):
    tokens = {
        NUMBER,
        STRING,
        IDENTIFIER,
        DEF,
        DO,
        END,
        IF,
        ELSE,
        CASE,
        OF,
        SPREAD,
        CONCAT,
        ELIF,
        INT_DIV,
        ENUM,
        STRUCT,
        NEWLINE,
        THEN,
    }
    literals = {
        "=",
        ".",
        "[",
        "]",
        ",",
        "{",
        "}",
        "(",
        ")",
        ":",
        "+",
        "-",
        ">",
        "<",
        "*",
        "/",
        ".",
    }
    DEF = r"def"
    DO = r"do"
    END = r"end"
    IF = r"if"
    ELSE = r"else"
    ELIF = r"elif"
    CASE = r"case"
    ENUM = r"enum"
    THEN = r"then"
    STRUCT = r"struct"
    OF = r"of"
    SPREAD = r"\.{3}"
    STRING = r"'[^(\\')]*?'"
    NUMBER = r"\d+"
    IDENTIFIER = r"\w+"
    CONCAT = r"\+{2}"
    INT_DIV = r"/{2}"
    ignore_comment = r"#.*\n"

    ignore = " \t"

    @_(r"\n+")
    def NEWLINE(self, t):
        self.lineno += len(t.value)


from typing import Callable, Protocol


class UwuParser(Parser):
    tokens = UwuLexer.tokens
    debugfile = "parser.out"

    @_("[ body ] { NEWLINE body }")
    def program(self, p):
        match p.body0, p.body1:
            case None,[]:
                return Program([],None)
            case body0, []:
                return Program([body0],None)
            case None,[*body]:
                return Program(body,None)
            case body0, [*body1]:
                return Program([body0,*body1],None)
            case _:
                raise TypeError(f"{p.body0=} {p.body1=}")

    @_("expr", "struct", "enum")
    def body(self, p):
        return p[0]

    precedence = (
        ("left", CONCAT),
        ("left", "+", "-"),
        ("left", "*", "/", INT_DIV),
        ("right", "UMINUS"),
    )

    @_(
        "do",
        "identifier",
        "literal",
        "_def",
        "_if",
        "call",
        "case_of",
        "variable_declaration",
        "binary_expr",
        "array",
        "tuple",
    )
    def expr(self, p):
        return p[0]

    @_(
        "'-' expr %prec UMINUS",
        "'(' expr ')'",
    )
    def expr(self, p):
        return p[1]

    @_(
        "expr CONCAT expr",
        "expr '+' expr",
        "expr '-' expr",
        "expr '/' expr",
        "expr '*' expr",
        "expr INT_DIV expr",
    )
    def binary_expr(self, p):
        return

    @_(
        "DO [ type ] [ expr ] { NEWLINE expr } END",
    )
    def do(self, p):
        match p.expr0, p.expr1:
            case None,[*body]:
                return Do(body,type=p.type)
            case body0, [*body1]:
                return Do([*body1, body0],type=p.type)
            case _:
                raise TypeError(f"{p.expr0=} {p.expr1=}")

    @_("DEF identifier '(' [ param ] { ',' param } ')' [ type ] do")
    def _def(self, p):
        return

    @_("':' identifier [ '<' identifier { ',' identifier } '>' ]")
    def type(self, p):
        return Type(p.identifier0)

    @_(
        "STRUCT identifier [ '<' identifier { ',' identifier } '>' ] '{' { identifier type } '}'"
    )
    def struct(self, p):
        return

    @_("ENUM identifier [ '<' identifier { ',' identifier } '>' ] '{' { enum_key } '}'")
    def enum(self, p):
        return

    @_("identifier [ '(' identifier { ',' identifier } ')' ]")
    def enum_key(self, p):
        return

    @_("identifier [ type ]")
    def param(self, p):
        return

    @_("IF expr THEN [ type ] [ expr ] { NEWLINE expr } { _elif } [ _else ] END")
    def _if(self, p):
        return

    @_("ELSE [ expr ] { NEWLINE expr }")
    def _else(self, p):
        return

    @_("ELIF expr THEN [ type ] [ expr ] { NEWLINE expr }")
    def _elif(self, p):
        return

    @_("CASE expr OF case { case } END")
    def case_of(self, p):
        return

    @_("pattern { ',' pattern } do")
    def case(self, p):
        return

    @_(
        "enum_pattern",
        "tuple_pattern",
        "array_pattern",
    )
    def pattern(self, p):
        return

    @_("'[' { pattern ',' } [ SPREAD identifier { ',' pattern } ] ']'")
    def array_pattern(self, p):
        return

    @_("identifier [ '(' pattern { ',' pattern } ')' ]")
    def enum_pattern(self, p):
        return

    @_("'{' { pattern ',' } [ SPREAD identifier { ',' pattern } ] '}'")
    def tuple_pattern(self, p):
        return

    @_("'[' [ expr ] { ',' expr } ']'")
    def array(self, p):
        return

    @_("'{' [ expr ] { ',' expr } '}'")
    def tuple(self, p):
        return

    @_("callee '(' [ expr ]  { ',' expr } ')'")
    def call(self, p):
        return

    @_("identifier")
    def callee(self, p):
        return

    @_("IDENTIFIER")
    def identifier(self, p):
        return Identifier(p.IDENTIFIER)

    @_("identifier [ type ] '=' expr")
    def variable_declaration(self, p):
        return VariableDeclaration(id=p.identifier,init=p.expr, type=p.type)

    @_("NUMBER")
    def literal(self, p):
        return Literal(p.NUMBER, float(p.NUMBER),Type(Identifier('number')))

    @_("STRING")
    def literal(self, p):
        return Literal(p.STRING,p.STRING,Type(Identifier('string')))


import json
import dataclasses


class AstEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return {"type": type(obj).__name__} | {
                field: getattr(obj, field) for field in obj.__dataclass_fields__
            }
        return json.JSONEncoder.default(self, obj)


import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        with open(event.src_path, "r") as f:
            data = f.read()

        ast = parser.parse(lexer.tokenize(data))

        if ast == None:
            return

        with open("ast.json", "w") as f:
            json.dump(ast, f, cls=AstEncoder, indent=4)


import json




@dataclasses.dataclass(frozen=True)
class VariableDeclaration(Generic[A,B]):
    id: A
    init:B 
    type: Type|None
    start:int|None=None
    end: int|None=None

@dataclasses.dataclass(frozen=True)
class Do(Generic[C]):
    body: list[C]
    type: Type|None
    start:int|None=None
    end: int|None=None
@dataclasses.dataclass(frozen=True)
class Literal:
    raw: str
    value: float|str
    type: Type
    start:int|None=None
    end: int|None=None

@dataclasses.dataclass(frozen=True)
class Program(Generic[D]):
    body: list[D]
    type: Type|None
    start:int|None=None
    end: int|None=None

@dataclasses.dataclass(frozen=True)
class Type(Generic[E]):
    raw: E
    @property
    def type(self):
        return self

    start:int|None=None
    end: int|None=None

@dataclasses.dataclass(frozen=True)
class Identifier:
    name: str
    start:int|None=None
    end: int|None=None


AstNode: TypeAlias = Program[R]| Do[R]|VariableDeclaration[R,R]|Type[R]
AstTree: TypeAlias = AstNode['AstTree']


scope = []


def type_visitor(node:AstTree) -> Type:
    print(f"{node=}")
    match node:
        case VariableDeclaration(id, init,None):
            return type_visitor(init)
        case VariableDeclaration(id, init,type) if type!=None:
            if type_visitor(init) != type:
                raise VisitorTypeException(f"{type_visitor(init)=} {type=} type mismatch")
            return type
        case Literal(type=type):
            return type
        case Program([],type) if type!=None:
            return type
        case Program(body,type):
            body = [type_visitor(b) for b in body]
            return body[-1]

        case Do([],None):
            raise VisitorTypeException(f"Type annotation missing for DO block line {node.start=} {node.end=}")
        case Do([],type):
            raise VisitorTypeException(f"Body missing for DO block line {node.start=} {node.end=}")
        case Do(body,None):
            scope.append({})
            body = [type_visitor(b) for b in body]
            scope.pop()
            return body[-1]

        case Do(body,type) if type!=None:
            scope.append({})
            body = [type_visitor(b) for b in body]

            if body[-1] != type:
                raise VisitorTypeException(f"Type missmatch for DO block {body[-1]=} {type=} line {node.start=} {node.end=}")
            
            scope.pop()
            return type
        case _:
            raise TypeError(f"{node=}")

class VisitorTypeException(Exception):
    pass

if __name__ == "__main__":
    lexer = UwuLexer()
    parser = UwuParser()

    with open("test.uwu", "r") as f:
        data = f.read()

    ast = parser.parse(lexer.tokenize(data))
