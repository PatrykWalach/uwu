from __future__ import annotations
from Unifier import unify

from constraint import collect


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
import dataclasses
from Annotate import Annotate
A = TypeVar("A")
R = TypeVar("R")


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
        "."
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
        return t


from typing import Callable, Protocol


def concat(v: A | None, l1: list[A]) -> list[A]:
    l0 = [] if v == None else [v]

    return l0 + l1


import terms


class UwuParser(Parser):
    tokens = UwuLexer.tokens
    debugfile = "parser.out"

    @_("[ stmt ] { NEWLINE stmt }")
    def program(self, p):
        return terms.EProgram(concat(p.stmt0, p.stmt1))

    @_("expr", "struct", "enum")
    def stmt(self, p):
        return p[0]

    precedence = (
        ("left", "="),
        ("left", CONCAT),
        ("left", "+", "-"),
        ("left", "*", "/", INT_DIV),
        ("right", "UMINUS"),
    )

    @_(
        "do",
        "identifier",
        "literal",
        "def_expr",
        "if_expr",
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
        return terms.EBinaryExpr(p[1], p[0], p[2])

    @_(
        "DO [ ':' type ] [ expr ] { NEWLINE expr } END",
    )
    def do(self, p):
        return terms.EDo(concat(p.expr0, p.expr1), hint=p.type)

    @_("DEF identifier '(' [ param ] { ',' param } ')' [ type ] do")
    def def_expr(self, p):
        return terms.EDef(
            p.identifier, concat(p.param0, p.param1), body=p.do, hint=p.type
        )

    @_("identifier [ '<' type { ',' type } '>' ]")
    def type(self, p):
        if p.identifier.name == "string":
            return typed.TStr()
        if p.identifier.name == "number":
            return typed.TNum()

        return typed.TGeneric(p.identifier.name, tuple(concat(p.type0, p.type1)))

    @_(
        "STRUCT identifier [ '<' identifier { ',' identifier } '>' ] '{' { identifier type } '}'"
    )
    def struct(self, p):
        return NotImplemented

    @_("ENUM identifier [ '<' identifier { ',' identifier } '>' ] '{' { enum_key } '}'")
    def enum(self, p):
        return NotImplemented

    @_("identifier [ '(' identifier { ',' identifier } ')' ]")
    def enum_key(self, p):
        return NotImplemented

    @_("identifier [ ':' type ]")
    def param(self, p):
        return terms.EParam(p.identifier, p.type)

    @_("IF expr THEN [ ':' type ] [ expr ] { NEWLINE expr } { elif_expr } [ else_expr ] END")
    def if_expr(self, p):
        return NotImplemented

    @_("ELSE [ expr ] { NEWLINE expr }")
    def else_expr(self, p):
        return NotImplemented

    @_("ELIF expr THEN [ ':' type ] [ expr ] { NEWLINE expr }")
    def elif_expr(self, p):
        return NotImplemented

    @_("CASE expr OF case { case } END")
    def case_of(self, p):
        return terms.ECaseOf(p.expr, concat(p.case0, p.case1))

    @_("pattern do")
    def case(self, p):
        return terms.ECase(p.pattern, p.do)

    @_(
        
        "enum_pattern",
        # "tuple_pattern",
        # "array_pattern",
    )
    def pattern(self, p):
        return p[0]

    # @_("'[' { pattern ',' } [ SPREAD identifier { ',' pattern } ] ']'")
    # def array_pattern(self, p):
    #     return terms.ArrayPattern(concat(p.pattern0, p.pattern1))

    @_("identifier [ '(' pattern { ',' pattern } ')' ]")
    def enum_pattern(self, p):
        print(f"{p[1]=}")
        if p[1] != None:
            return terms.EEnumPattern(p.identifier, [p[1][1]] + p[1][2])
        return terms.EEnumPattern(p.identifier, [])

    # @_("'{' { pattern ',' } [ SPREAD identifier { ',' pattern } ] '}'")
    # def tuple_pattern(self, p):
    #     return NotImplemented

    @_("'[' [ expr ] { ',' expr } ']'")
    def array(self, p):
        return NotImplemented

    @_("'{' [ expr ] { ',' expr } '}'")
    def tuple(self, p):
        return NotImplemented

    @_("callee '(' [ expr ]  { ',' expr } ')'")
    def call(self, p):
        return terms.ECall(p.callee, concat(p.expr0, p.expr1))

    @_("identifier")
    def callee(self, p):
        return p[0]

    @_("IDENTIFIER")
    def identifier(self, p):
        return terms.EIdentifier(p.IDENTIFIER)

    @_("identifier [ ':' type ] '=' expr")
    def variable_declaration(self, p):
        return terms.EVariableDeclaration(id=p.identifier, init=p.expr, hint=p.type)

    @_("NUMBER")
    def literal(self, p):
        return terms.ELiteral(p.NUMBER, float(p.NUMBER))

    @_("STRING")
    def literal(self, p):
        return terms.ELiteral(p.STRING, p.STRING[1:-1])


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

def infer(program):
    typed_term = Annotate({})(program)
    constraints = collect(typed_term)
    subst = unify(constraints)
    return subst.apply_type(typed_term.ty)

if __name__ == "__main__":
    lexer = UwuLexer()
    parser = UwuParser()

    with open("test.uwu", "r") as f:
        data = f.read()

    ast = parser.parse(
        lexer.tokenize(
            "def id(a) do a(1,2) end"
        )
    )

    if ast != None:

        with open("ast.json", "w") as f:
            json.dump(infer(ast), f, cls=AstEncoder, indent=4)
        
        


