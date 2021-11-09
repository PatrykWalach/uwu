from __future__ import annotations

def _(fn: str, *args: str) -> Callable[[R], R]:
    raise Exception

from sly import Parser, Lexer
import functools
import json
import operator
import random
from functools import partial, reduce, wraps
from itertools import product
from typing import Any, Callable, Generic, TypeAlias, TypeVar, Union, overload
import typed
import terms
from typed_terms import TypedDo,TypedIdentifier,TypedLiteral,TypedProgram,TypedVariableDeclaration
import dataclasses
A = TypeVar('A')
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
    CONCAT = r"\+{2}"
    INT_DIV = r"/{2}"
    IDENTIFIER = r"\w+"

    ignore_comment = r"\#.*"
    ignore = " \t"

    @_(r"\n+")
    def NEWLINE(self, t):
        self.lineno += len(t.value)


from typing import Callable, Protocol


def concat(v: A|None, l1:list[A])->list[A]:
    l0 = [] if v == None else [v]
    
    return l0 + l1
import terms
class UwuParser(Parser):
    tokens = UwuLexer.tokens
    debugfile = "parser.out"

    @_("[ body ] { NEWLINE body }")
    def program(self, p):
        match p.body0, p.body1:
            case body0, [*body1]:
                return terms.Program(concat(body0, body1))
            case _:
                raise TypeError(f"{p.body0=} {p.body1=}")

    @_("expr", "struct", "enum")
    def body(self, p):
        return p[0]

    precedence = (
        ("left", CONCAT),
        ("left", "+", "-"),
        ("left", "*", "/", INT_DIV),
        ('left','='),
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
        return terms.BinaryExpr(p[1],p[0], p[2])

    @_(
        "DO [ type ] [ expr ] { NEWLINE expr } END",
    )
    def do(self, p):
        match p.type, p.expr0, p.expr1:
            case None, body0, [*body1]:
                return terms.Do(concat(body0, body1))
            case type, body0, [*body1]:
                return TypedDo(concat(body0, body1), type)
            case _:
                raise TypeError(f"{p.expr0=} {p.expr1=}")

    @_("DEF identifier '(' [ param ] { ',' param } ')' [ type ] do")
    def _def(self, p):
        return

    @_("':' identifier [ '<' identifier { ',' identifier } '>' ]")
    def type(self, p):
        if p.identifier0.name == 'string':
            return typed.string()
        if p.identifier0.name == 'number':
            return typed.number()
        return typed.GenericType(p.identifier0.name,[])

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
        return terms.Identifier(p.IDENTIFIER)

    @_("identifier [ type ] '=' expr")
    def variable_declaration(self, p):
        if p.type ==None:
            return terms.VariableDeclaration(id=p.identifier,init=p.expr)
        return TypedVariableDeclaration(id=p.identifier,init=p.expr, type=p.type)

    @_("NUMBER")
    def literal(self, p):
        return terms.Literal(p.NUMBER, float(p.NUMBER))

    @_("STRING")
    def literal(self, p):
        return terms.Literal(p.STRING,p.STRING)


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






scope = []



if __name__ == "__main__":
    lexer = UwuLexer()
    parser = UwuParser()

    with open("test.uwu", "r") as f:
        data = f.read()

    ast = parser.parse(lexer.tokenize(data))
