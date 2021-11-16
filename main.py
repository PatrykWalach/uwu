from __future__ import annotations
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import time
import sys
from typing import Callable, Protocol
import dataclasses
from algorithm_j import Context, Scheme, fresh_ty_var, type_infer
import terms
import typed
from typing import Any, Callable, Generic, TypeAlias, TypeVar, Union, overload
from itertools import product
from functools import partial, reduce, wraps
import random
import operator
import json
import functools
from sly import Parser, Lexer


def _(fn: str, *args: str) -> Callable[[R], R]:
    raise Exception


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
        NOT_LESS,
        NOT_MORE, TYPE_IDENTIFIER
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
    SPREAD = r"\.{3}"
    STRING = r"'[^(\\')]*?'"
    NUMBER = r"\d+"
    CONCAT = r"\+{2}"
    NOT_LESS = r">="
    NOT_MORE = r"<="
    INT_DIV = r"/{2}"
    TYPE_IDENTIFIER = r"[A-Z]\w*"
    IDENTIFIER = r"[a-z]\w*"
    IDENTIFIER["def"] = DEF
    IDENTIFIER["do"] = DO
    IDENTIFIER["end"] = END
    IDENTIFIER["if"] = IF
    IDENTIFIER["else"] = ELSE
    IDENTIFIER["elif"] = ELIF
    IDENTIFIER["case"] = CASE
    IDENTIFIER["enum"] = ENUM
    IDENTIFIER["then"] = THEN
    IDENTIFIER["struct"] = STRUCT
    IDENTIFIER["of"] = OF

    ignore_comment = r"\#.*"
    ignore = " \t"

    @_(r"\n+")
    def NEWLINE(self, t):
        self.lineno += len(t.value)
        return t


def concat(v: A | None, l1: list[A] | None) -> list[A]:
    l0 = [] if v == None else [v]
    l1 = l1 if isinstance(l1, list) else []
    return l0 + l1


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
        ("left", "<", ">",
         NOT_LESS, NOT_MORE
         ),
        ("left", CONCAT),
        ("left", "+", "-"),
        ("left", "*", "/", INT_DIV),
        ("right", "UMINUS"),
    )

    @_(
        "do",
        "literal",
        "def_expr",
        "if_expr",
        "call",
        "case_of",
        "variable_declaration",
        "identifier", 'type_identifier',
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
        "expr '<' expr",
        "expr '>' expr",
        "expr NOT_LESS expr",
        "expr NOT_MORE expr",
        "expr INT_DIV expr",
    )
    def binary_expr(self, p):
        return terms.EBinaryExpr(p[1], p[0], p[2])

    @_(
        "DO [ ':' type ] [ expr ] { NEWLINE expr } END",
    )
    def do(self, p):
        return terms.EDo(concat(p.expr0, p.expr1), hint=p.type)

    @_(
        "[ expr ] { NEWLINE expr }",
    )
    def block_statement(self, p):
        return terms.EBlockStmt(concat(p.expr0, p.expr1))

    @_("DEF identifier '(' [ param ] { ',' param } ')' [ ':' type ] do")
    def def_expr(self, p):
        return terms.EDef(
            p.identifier, concat(p.param0, p.param1), body=p.do, hint=p.type
        )

    @_("type_identifier [ '<' type { ',' type } '>' ]")
    def type(self, p):
        print(f"{p[1]=}")
        return terms.EHint(p.type_identifier, concat(p[1][1], p[1][2]))

    @_(
        "STRUCT type_identifier [ '<' identifier { ',' identifier } '>' ] '{' { identifier ':' type } '}'"
    )
    def struct(self, p):
        raise NotImplemented

    @_("ENUM type_identifier [ '<' fields_unnamed '>' ] '{' { variant } '}'")
    def enum(self, p):
        return terms.EEnumDeclaration(p.type_identifier, p.fields_unnamed, p.variant)

    @_("type_identifier [ '(' fields_unnamed ')' ]")
    def variant(self, p):
        return terms.EVariant(p.identifier, terms.EFieldsUnnamed(p.fields_unnamed))

    @_("identifier { ',' identifier }")
    def fields_unnamed(self, p):
        return concat(p.identifier0, p.identifier1)

    @_("identifier [ ':' type ]")
    def param(self, p):
        return terms.EParam(p.identifier, p.type)

    @_("IF expr THEN [ ':' type ] block_statement [ or_else ] END")
    def if_expr(self, p):
        return terms.EIf(p.expr,
                         then=p.block_statement,
                         or_else=p.or_else,
                         hint=p.type)

    @_("ELSE block_statement")
    def or_else(self, p):
        return p.block_statement

    @_("ELIF expr THEN block_statement [ or_else ]")
    def or_else(self, p):
        return terms.EIf(p.expr,
                         then=p.block_statement,
                         or_else=p.or_else)

    @_("CASE expr OF case { case } END")
    def case_of(self, p):
        return terms.ECaseOf(p.expr, concat(p.case0, p.case1))

    @_("pattern do")
    def case(self, p):
        return terms.ECase(p.pattern, p.do)

    @_(
        "identifier",
        "enum_pattern",
        # "tuple_pattern",
        # "array_pattern",
    )
    def pattern(self, p):
        return p[0]

    # @_("'[' { pattern ',' } [ SPREAD identifier { ',' pattern } ] ']'")
    # def array_pattern(self, p):
    #     return terms.ArrayPattern(concat(p.pattern0, p.pattern1))

    @_("type_identifier [ '(' pattern { ',' pattern } ')' ]")
    def enum_pattern(self, p):

        return terms.EEnumPattern(p.type_identifier, concat(p.pattern0, concat(p.pattern1, [])  # p[1][1], concat(p[1][2], [])
                                                            ))

    @_("TYPE_IDENTIFIER")
    def type_identifier(self, p):
        return terms.EIdentifier(p.TYPE_IDENTIFIER)

    # @_("'{' { pattern ',' } [ SPREAD identifier { ',' pattern } ] '}'")
    # def tuple_pattern(self, p):
    #     raise NotImplemented

    @_("'[' [ expr ] { ',' expr } ']'")
    def array(self, p):
        raise NotImplemented

    @_("'{' [ expr ] { ',' expr } '}'")
    def tuple(self, p):
        raise NotImplemented

    @_("callee '(' [ expr ]  { ',' expr } ')'")
    def call(self, p):
        return terms.ECall(p.callee, concat(p.expr0, p.expr1))

    @_("identifier", 'type_identifier')
    def callee(self, p):
        return p[0]

    @_("IDENTIFIER")
    def identifier(self, p):
        return terms.EIdentifier(p.IDENTIFIER)

    @_("identifier [ ':' type ] '=' expr")
    def variable_declaration(self, p):
        return terms.EVariableDeclaration(id=p.identifier, init=p.expr, hint=p.type)

    @_("identifier ':' type_identifier '<' type { ',' type } NOT_LESS expr")
    def variable_declaration(self, p):
        return terms.EVariableDeclaration(id=p.identifier, init=p.expr, hint=terms.EHint(p.type_identifier, concat(p.type0, p.type1)))

    @_("NUMBER")
    def literal(self, p):
        return terms.ELiteral(p.NUMBER, float(p.NUMBER))

    @_("STRING")
    def literal(self, p):
        return terms.ELiteral(p.STRING, p.STRING[1:-1])


class AstEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return {"type": type(obj).__name__} | {
                field: getattr(obj, field) for field in obj.__dataclass_fields__
            }
        return json.JSONEncoder.default(self, obj)


class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        with open(event.src_path, "r") as f:
            data = f.read()

        ast = parser.parse(lexer.tokenize(data))

        if ast == None:
            return

        with open("ast.json", "w") as f:
            json.dump(ast, f, cls=AstEncoder, indent=4)


ty_some = typed.TVar(-2)
ty_id = typed.TVar(-1)

DEFAULT_CTX: Context = {
    'Str': Scheme([], typed.TStr()),
    'Num': Scheme([], typed.TNum()),
    'None': Scheme([], typed.TGeneric('Option', [fresh_ty_var()])), 'Some': Scheme([ty_some.type],  typed.TDef([ty_some], typed.TGeneric('Option', [ty_some]))),
    'id': Scheme([ty_id.type], typed.TDef([ty_id], ty_id)),
    'Option': Scheme([], typed.TGeneric('Option', [fresh_ty_var()])),
}


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
            json.dump(type_infer(DEFAULT_CTX, ast),
                      f, cls=AstEncoder, indent=4)
