from __future__ import annotations

import dataclasses
import functools
import json
import operator
import random
import sys

# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer
import time
from functools import partial, reduce, wraps
from itertools import product
from typing import Any, Callable, Generic, Protocol, TypeAlias, TypeVar, Union, overload

from sly import Lexer, Parser

import terms
import typed
from algorithm_j import Context, Scheme, fresh_ty_var, type_infer


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
        CONCAT,
        ELIF,
        INT_DIV,
        ENUM,
        THEN,
        TYPE_IDENTIFIER,
        LET,
        EXTERNAL,
        NOT_EQUAL,
        EQUAL,
        NEWLINE,
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
        "|",
        "%",
    }
    NOT_EQUAL = r"!="
    EQUAL = r"=="
    STRING = r"'[^']*'"
    NUMBER = r"\d+"
    CONCAT = r"\+{2}"
    INT_DIV = r"/{2}"
    TYPE_IDENTIFIER = r"[A-Z\d][\w\d]*"
    IDENTIFIER = r"[a-z_][\w\d]*"
    IDENTIFIER["def"] = DEF
    IDENTIFIER["do"] = DO
    IDENTIFIER["end"] = END
    IDENTIFIER["if"] = IF
    IDENTIFIER["else"] = ELSE
    IDENTIFIER["elif"] = ELIF
    IDENTIFIER["case"] = CASE
    IDENTIFIER["enum"] = ENUM
    IDENTIFIER["then"] = THEN

    IDENTIFIER["of"] = OF
    IDENTIFIER["let"] = LET
    EXTERNAL = r"`[^`]*`"

    ignore_comment = r"\#.*"
    ignore = " \t"

    @_(r"\n([\s\t\n]|\#.*)*")
    def NEWLINE(self, t):
        self.lineno += t.value.count("\n")
        return t


def concat(v: A | None, l1: list[A] | None) -> list[A]:
    l0 = [] if v == None else [v]
    l1 = l1 if isinstance(l1, list) else []
    return l0 + l1


class UwuParser(Parser):
    tokens = UwuLexer.tokens
    debugfile = "parser.out"

    @_("[ NEWLINE ] [ do_exprs ]")
    def program(self, p):
        return terms.EProgram(p.do_exprs or [])

    @_("expr NEWLINE do_exprs")
    def do_exprs(self, p):
        return [p.expr] + p.do_exprs

    @_("expr [ NEWLINE ]")
    def do_exprs(self, p):
        return [p.expr]

    precedence = (
        ("left", "="),
        ("left", "NOT_EQUAL", "EQUAL"),
        ("left", "<", ">"),
        ("left", "+", "-", "|", "CONCAT"),
        ("left", "*", "/", "INT_DIV", "%"),
        ("right", "UMINUS"),
        ("left", "(", ")"),
        # ('left', 'V_CALL'),
        # ('right', 'CALL')
    )

    @_(
        "enum",
        "external",
        "do",
        "literal",
        "def_expr",
        "if_expr",
        "binary_expr",
        "case_of",
        "call",
        "variable_declaration",
        "identifier",
        "variant_call",
        "array",
        # "tuple",
    )
    def expr(self, p):
        return p[0]

    @_(
        "'(' expr ')'",
    )
    def expr(self, p):
        return p[1]

    @_(
        "'-' expr %prec UMINUS",
    )
    def expr(self, p):
        return terms.EUnaryExpr(p[0], p.expr)

    @_("EXTERNAL")
    def external(self, p):
        return terms.EExternal(p.EXTERNAL[1:-1])

    @_(
        "expr CONCAT expr",
        "expr '+' expr",
        "expr '-' expr",
        "expr '/' expr",
        "expr '*' expr",
        "expr '<' expr",
        "expr '%' expr",
        "expr '>' expr",
        "expr '|' expr",
        "expr NOT_EQUAL expr",
        "expr EQUAL expr",
        "expr INT_DIV expr",
    )
    def binary_expr(self, p):
        return terms.EBinaryExpr(p[1], p[0], p[2])

    @_(
        "DO [ ':' type ] [ NEWLINE ] [ do_exprs ] END",
    )
    def do(self, p):
        return terms.EDo(p.do_exprs or [], hint=terms.EHint.from_option(p.type))

    @_(
        "[ NEWLINE ] [ do_exprs ]",
    )
    def block_statement(self, p):
        return terms.EBlock(p.do_exprs or [])

    @_(
        "DEF identifier '<' type_identifier { ',' type_identifier } '>' '(' [ NEWLINE ] [ params ] ')' [ ':' type ] do"
    )
    def def_expr(self, p):
        return terms.EDef(
            p.identifier.name,
            p.params or [],
            body=p.do,
            hint=terms.EHint.from_option(p.type),
            generics=concat(p.type_identifier0, p.type_identifier1),
        )

    @_("DEF identifier '(' [ NEWLINE ] [ params ] ')' [ ':' type ] do")
    def def_expr(self, p):
        return terms.EDef(
            p.identifier.name,
            p.params or [],
            body=p.do,
            hint=terms.EHint.from_option(p.type),
        )

    @_("params ',' [ NEWLINE ] param [ NEWLINE ]")
    def params(self, p):
        return p.params + [p.param]

    @_("param [ NEWLINE ]")
    def params(self, p):
        return [p.param]

    @_("type_identifier")
    def type(self, p):
        return terms.EHint(p.type_identifier.name, [])

    @_("type_identifier '<' type { ',' type } '>'")
    def type(self, p):
        return terms.EHint(p.type_identifier.name, concat(p.type0, p.type1))

    @_(
        "ENUM type_identifier '<' type_identifier { ',' type_identifier } '>' '{' [ NEWLINE ] [ variants ] '}'"
    )
    def enum(self, p):
        return terms.EEnumDeclaration(
            p.type_identifier0.name,
            p.variants or [],
            concat(p.type_identifier1, p.type_identifier2),
        )

    @_("variants variant [ NEWLINE ]")
    def variants(self, p):
        return p.variants + [p.variant]

    @_("variant [ NEWLINE ]")
    def variants(self, p):
        return [p.variant]

    @_("ENUM type_identifier '{' [ NEWLINE ] [ variants ] '}'")
    def enum(self, p):
        return terms.EEnumDeclaration(p.type_identifier.name, p.variants or [])

    @_("type_identifier '(' type  { ',' type } ')'")
    def variant(self, p):
        return terms.EVariant(p.type_identifier.name, concat(p.type0, p.type1))

    @_("type_identifier")
    def variant(self, p):
        return terms.EVariant(p.type_identifier.name)

    # @_("identifier { ',' identifier }")
    # def fields_unnamed(self, p):
    #     return concat(p.identifier0, p.identifier1)

    @_("identifier [ ':' type ]")
    def param(self, p):
        return terms.EParam(p.identifier.name, terms.EHint.from_option(p.type))

    @_("IF expr THEN [ ':' type ] block_statement [ or_else ] END")
    def if_expr(self, p):
        return terms.EIf(
            p.expr,
            then=p.block_statement,
            or_else=terms.EIf.from_option(p.or_else),
            hint=terms.EHint.from_option(p.type),
        )

    @_("ELSE block_statement")
    def or_else(self, p):
        return p.block_statement

    @_("ELIF expr THEN block_statement [ or_else ]")
    def or_else(self, p):
        return terms.EIf(
            p.expr, then=p.block_statement, or_else=terms.EIf.from_option(p.or_else)
        )

    @_("CASE expr OF [ NEWLINE ] [ cases ] END")
    def case_of(self, p):
        return terms.ECaseOf(p.expr, p.cases or [])

    @_("cases pattern do [ NEWLINE ]")
    def cases(self, p):
        return p.cases + [terms.ECase({"$": p.pattern}, p.do)]

    @_("pattern do [ NEWLINE ]")
    def cases(self, p):
        return [terms.ECase({"$": p.pattern}, p.do)]

    # @_("clause { ',' clause } do")
    # def case(self, p):
    #     import operator

    #     return terms.ECase(
    #         functools.reduce(operator.__or__, concat(p.clause0, p.clause1)), p.do
    #     )

    # @_("identifier '=' pattern")
    # def clause(self, p):
    #     return {p.identifier.name: p.pattern}

    @_("match_as", "match_variant")  # , "tuple_pattern", "array_pattern"
    def pattern(self, p):
        return p[0]

    @_("identifier")
    def match_as(self, p):
        return terms.EMatchAs(p.identifier.name)

    # @_("'[' [ pattern ] { ',' pattern } ']'")
    # def array_pattern(self, p):
    #     return terms.EMatchArray(concat(p.pattern0, p.pattern1))

    # @_("'{' [ pattern ] { ',' pattern } '}'")
    # def tuple_pattern(self, p):
    #     return terms.EMatchTuple(concat(p.pattern0, p.pattern1))

    @_("type_identifier '(' [ NEWLINE ] [ patterns ] ')'")
    def match_variant(self, p):
        return terms.EMatchVariant(p.type_identifier.name, p.patterns or [])

    @_("type_identifier")
    def match_variant(self, p):
        return terms.EMatchVariant(p.type_identifier.name, [])

    @_("patterns ',' [ NEWLINE ] pattern [ NEWLINE ]")
    def patterns(self, p):
        return p.patterns + [p.pattern]

    @_("pattern [ NEWLINE ]")
    def patterns(self, p):
        return [p.pattern]

    @_("'[' [ NEWLINE ] [ exprs ] ']'")
    def array(self, p):
        return terms.EArray(p.exprs or [])

    # @_("'{' [ expr ] { ',' expr } '}'")
    # def tuple(self, p):
    #     return terms.ETuple(concat(p.expr0, p.expr1))

    @_("expr '(' [ NEWLINE ] [ exprs ] ')'")
    def call(self, p):
        return terms.ECall(p.expr, p.exprs or [])

    @_("type_identifier '(' [ NEWLINE ] [ exprs ] ')'")
    def variant_call(self, p):
        return terms.EVariantCall(p.type_identifier.name, p.exprs or [])

    @_("exprs ',' [ NEWLINE ] expr [ NEWLINE ]")
    def exprs(self, p):
        return p.exprs + [p.expr]

    @_("expr [ NEWLINE ]")
    def exprs(self, p):
        return [p.expr]

    @_("IDENTIFIER")
    def identifier(self, p):
        return terms.EIdentifier(p.IDENTIFIER)

    @_("TYPE_IDENTIFIER")
    def type_identifier(self, p):
        return terms.EIdentifier(p.TYPE_IDENTIFIER)

    @_("LET identifier [ ':' type ] '=' expr")
    def variable_declaration(self, p):
        return terms.ELet(
            id=p.identifier.name, init=p.expr, hint=terms.EHint.from_option(p.type)
        )

    @_("NUMBER")
    def literal(self, p):
        return terms.ELiteral(float(p.NUMBER))

    @_("STRING")
    def literal(self, p):
        return terms.ELiteral(p.STRING[1:-1])
