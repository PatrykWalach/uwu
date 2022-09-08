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

import sly  # type: ignore[import]
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
        "INT",
        "FLOAT",
        "STRING",
        "IDENTIFIER",
        "DEF",
        "DO",
        "END",
        "IF",
        "ELSE",
        "CASE",
        "OF",
        "CONCAT",
        "ELIF",
        "ENUM",
        "THEN",
        "TYPE_IDENTIFIER",
        "EXTERNAL",
        "FLOAT_SUM",
        "FLOAT_SUB",
        "FLOAT_DIV",
        "FLOAT_MUL",
        "NOT_EQUAL",
        "EQUAL",
        "NEWLINE",
        "STRICT_OR",
        "STRICT_AND",
        "STRICT_NOT",
        "OR",
        "AND",
        "TEXT_MATCH",
        "LESS_OR_EQ",
        "MORE_OR_EQ",
        "ARRAY_CONCAT",
        "ARRAY_SUB",
        "POW",
        "FLOAT_POW",
        "BIT_OR",
        "BIT_AND",
        "BIT_SHIFT_LEFT",
        # "BIT_SHIFT_RIGHT", TODO 1: fix A<A<A<B>>> +bug
        "DOUBLE_ARROW_LEFT",
        "DOUBLE_ARROW_RIGHT",
        "ARROW_LEFT",
        "ARROW_RIGHT",
        "ARROW_BOTH",
        "SOME_CONCAT",
        "SOME_SUB",
        "FLOAT_LESS_OR_EQ",
        "FLOAT_LESS",
        "FLOAT_MORE_OR_EQ",
        "FLOAT_MORE",
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
        "!",
    }
    OR = r"\|\|"
    AND = r"&&"
    TEXT_MATCH = r"=~"
    FLOAT_LESS_OR_EQ = r"<=\."
    FLOAT_LESS = r"<\."
    FLOAT_MORE_OR_EQ = r">=\."
    FLOAT_MORE = r">\."
    LESS_OR_EQ = r"<="
    MORE_OR_EQ = r">="
    ARRAY_CONCAT = r"\+\+"
    ARRAY_SUB = r"--"
    FLOAT_POW = r"\*\*\."
    POW = r"\*\*"

    BIT_OR = r"\|\|\|"
    BIT_AND = r"&&&"
    BIT_SHIFT_LEFT = r"<<<"
    # BIT_SHIFT_RIGHT = r">>>"
    DOUBLE_ARROW_LEFT = r"<<~"
    DOUBLE_ARROW_RIGHT = r"~>>"
    ARROW_LEFT = r"<~"
    ARROW_RIGHT = r"~>"
    ARROW_BOTH = r"<~>"
    SOME_CONCAT = r"\+\+\+"
    SOME_SUB = r"---"

    NOT_EQUAL = r"!="
    EQUAL = r"=="
    STRING = r"'[^']*'"
    FLOAT = r"\d[\d_]*\.[\d_]*"
    INT = r"\d[\d_]*"
    CONCAT = r"<>"
    FLOAT_SUM = r"\+\."
    FLOAT_SUB = r"-\."
    FLOAT_DIV = r"/\."
    FLOAT_MUL = r"\*\."
    TYPE_IDENTIFIER = r"[A-Z\d][\w\d]*"
    IDENTIFIER = r"[a-z_][\w\d]*"
    IDENTIFIER["def"] = "DEF"  # type: ignore[index]
    IDENTIFIER["do"] = "DO"  # type: ignore[index]
    IDENTIFIER["end"] = "END"  # type: ignore[index]
    IDENTIFIER["if"] = "IF"  # type: ignore[index]
    IDENTIFIER["else"] = "ELSE"  # type: ignore[index]
    IDENTIFIER["elif"] = "ELIF"  # type: ignore[index]
    IDENTIFIER["case"] = "CASE"  # type: ignore[index]
    IDENTIFIER["enum"] = "ENUM"  # type: ignore[index]
    IDENTIFIER["then"] = "THEN"  # type: ignore[index]
    IDENTIFIER["of"] = "OF"  # type: ignore[index]
    IDENTIFIER["or"] = "STRICT_OR"  # type: ignore[index]
    IDENTIFIER["and"] = "STRICT_AND"  # type: ignore[index]
    IDENTIFIER["not"] = "STRICT_NOT"  # type: ignore[index]

    EXTERNAL = r"`[^`]*`"

    ignore_comment = r"\#.*"
    ignore = " \t"

    @_(r"\n([\s\t\n]|\#.*)*")
    def NEWLINE(self, t):
        self.lineno += t.value.count("\n")
        return t


def concat(v: A | None, l1: list[A] | None) -> list[A]:
    l0 = [] if v is None else [v]
    l2 = l1 if isinstance(l1, list) else []
    return l0 + l2


class UwuParser(Parser):
    tokens = UwuLexer.tokens
    debugfile = "parser.out"

    @_("[ NEWLINE ] [ do_exprs ]")
    def program(self, p: sly.yacc.YaccProduction) -> terms.EProgram:
        return terms.EProgram(p.do_exprs or [])

    @_("expr NEWLINE do_exprs")
    def do_exprs(self, p: sly.yacc.YaccProduction) -> list[terms.EExpr]:
        return [p.expr] + p.do_exprs

    @_("expr [ NEWLINE ]")  # type: ignore[no-redef]
    def do_exprs(self, p: sly.yacc.YaccProduction) -> list[terms.EExpr]:
        return [p.expr]

    precedence = (
        ("right", "="),
        ("left", "OR", "STRICT_OR", "BIT_OR"),
        ("left", "AND", "STRICT_AND", "BIT_AND"),
        ("left", "NOT_EQUAL", "EQUAL", "TEXT_MATCH"),
        (
            "left",
            "<",
            ">",
            "LESS_OR_EQ",
            "MORE_OR_EQ",
            "FLOAT_LESS",
            "FLOAT_MORE",
            "FLOAT_LESS_OR_EQ",
            "FLOAT_MORE_OR_EQ",
        ),
        (
            "left",
            # "BIT_SHIFT_RIGHT",
            "BIT_SHIFT_LEFT",
            "DOUBLE_ARROW_RIGHT",
            "DOUBLE_ARROW_LEFT",
            "ARROW_RIGHT",
            "ARROW_LEFT",
            "ARROW_BOTH",
        ),
        ("right", "CONCAT", "ARRAY_CONCAT", "ARRAY_SUB", "SOME_CONCAT", "SOME_SUB"),
        ("left", "+", "-", "FLOAT_SUM", "FLOAT_SUB"),
        ("left", "*", "/", "FLOAT_DIV", "FLOAT_MUL"),
        ("left", "POW", "FLOAT_POW"),
        ("right", "UNARY"),
        ("left", "(", ")"),
    )

    @_(
        "enum",
        "external",
        "do",
        "def_expr",
        "if_expr",
        "binary_expr",
        "case_of",
        "call",
        "let",
        "identifier",
        "variant_call",
        "array",
        "int_literal",
        "float_literal",
        "str_literal",
        "unary_expr",
        "binary_op_def",
    )
    def expr(self, p: sly.yacc.YaccProduction) -> terms.EExpr:
        return terms.EExpr(p[0])

    @_(  # type: ignore[no-redef]
        "'(' expr ')'",
    )
    def expr(self, p: sly.yacc.YaccProduction) -> terms.EExpr:
        return p[1]

    @_(  # type: ignore[no-redef]
        "'-' expr %prec UNARY",
        "STRICT_NOT expr %prec UNARY",
        "'!' expr %prec UNARY",
        "'+' expr %prec UNARY",
    )
    def unary_expr(self, p: sly.yacc.YaccProduction) -> terms.EUnaryExpr:
        return terms.EUnaryExpr(p[0], p.expr)

    @_("EXTERNAL")
    def external(self, p: sly.yacc.YaccProduction) -> terms.EExternal:
        return terms.EExternal(p.EXTERNAL[1:-1])

    @_(
        "expr CONCAT expr",
        "expr '+' expr",
        "expr '-' expr",
        "expr '/' expr",
        "expr '*' expr",
        "expr '<' expr",
        "expr FLOAT_SUM expr",
        "expr FLOAT_SUB expr",
        "expr FLOAT_DIV expr",
        "expr FLOAT_MUL expr",
        "expr '>' expr",
        "expr NOT_EQUAL expr",
        "expr EQUAL expr",
        "expr OR expr",
        "expr STRICT_OR expr",
        "expr AND expr",
        "expr STRICT_AND expr",
        "expr TEXT_MATCH expr",
        "expr LESS_OR_EQ expr",
        "expr MORE_OR_EQ expr",
        "expr ARRAY_CONCAT expr",
        "expr ARRAY_SUB expr",
        "expr POW expr",
        "expr FLOAT_POW expr",
        "expr BIT_OR expr",
        "expr BIT_AND expr",
        "expr BIT_SHIFT_LEFT expr",
        # "expr BIT_SHIFT_RIGHT expr",
        "expr DOUBLE_ARROW_LEFT expr",
        "expr DOUBLE_ARROW_RIGHT expr",
        "expr ARROW_LEFT expr",
        "expr ARROW_RIGHT expr",
        "expr ARROW_BOTH expr",
        "expr SOME_CONCAT expr",
        "expr SOME_SUB expr",
        "expr FLOAT_LESS_OR_EQ expr",
        "expr FLOAT_LESS expr",
        "expr FLOAT_MORE_OR_EQ expr",
        "expr FLOAT_MORE expr",
    )
    def binary_expr(self, p: sly.yacc.YaccProduction):
        return terms.EBinaryExpr(p[1], p[0], p[2])

    @_(
        "CONCAT",
        "'+'",
        "'-'",
        "'/'",
        "'*'",
        "'<'",
        "FLOAT_SUM",
        "FLOAT_SUB",
        "FLOAT_DIV",
        "FLOAT_MUL",
        "'>'",
        "NOT_EQUAL",
        "EQUAL",
        "OR",
        "STRICT_OR",
        "AND",
        "STRICT_AND",
        "TEXT_MATCH",
        "LESS_OR_EQ",
        "MORE_OR_EQ",
        "ARRAY_CONCAT",
        "ARRAY_SUB",
        "POW",
        "FLOAT_POW",
        "BIT_OR",
        "BIT_AND",
        "BIT_SHIFT_LEFT",
        # "BIT_SHIFT_RIGHT",
        "DOUBLE_ARROW_LEFT",
        "DOUBLE_ARROW_RIGHT",
        "ARROW_LEFT",
        "ARROW_RIGHT",
        "ARROW_BOTH",
        "SOME_CONCAT",
        "SOME_SUB",
        "FLOAT_LESS_OR_EQ",
        "FLOAT_LESS",
        "FLOAT_MORE_OR_EQ",
        "FLOAT_MORE",
    )
    def binary_op(self, p: sly.yacc.YaccProduction) -> str:
        return p[0]

    @_(
        "DEF binary_op '<' type_identifier { ',' type_identifier } '>' '(' [ NEWLINE ] param ',' [ NEWLINE ] param [ NEWLINE ] ')' [ ':' type ] do"
    )
    def binary_op_def(self, p: sly.yacc.YaccProduction):
        return terms.EBinaryOpDef(
            p.binary_op,
            [p.param0, p.param1],
            body=p.do,
            hint=terms.MaybeEHint(p.type or terms.MaybeEHintNothing()),
            generics=concat(p.type_identifier0, p.type_identifier1),
        )

    @_("DEF binary_op '(' [ NEWLINE ] param ',' [ NEWLINE ] param [ NEWLINE ] ')' [ ':' type ] do")  # type: ignore[no-redef]
    def binary_op_def(self, p: sly.yacc.YaccProduction):
        return terms.EBinaryOpDef(
            p.binary_op,
            [p.param0, p.param1],
            body=p.do,
            hint=terms.MaybeEHint(p.type or terms.MaybeEHintNothing()),
        )

    @_(
        "DO [ ':' type ] block_statement END",
    )
    def do(self, p: sly.yacc.YaccProduction):
        return terms.EDo(
            p.block_statement,
            hint=terms.MaybeEHint(p.type or terms.MaybeEHintNothing()),
        )

    @_(
        "[ NEWLINE ] [ do_exprs ]",
    )
    def block_statement(self, p: sly.yacc.YaccProduction):
        return terms.EBlock(p.do_exprs or [])

    @_(
        "DEF identifier '<' type_identifier { ',' type_identifier } '>' '(' [ NEWLINE ] [ params ] ')' [ ':' type ] do"
    )
    def def_expr(self, p: sly.yacc.YaccProduction):
        return terms.EDef(
            p.identifier.name,
            p.params or [],
            body=p.do,
            hint=terms.MaybeEHint(p.type or terms.MaybeEHintNothing()),
            generics=concat(p.type_identifier0, p.type_identifier1),
        )

    @_("DEF identifier '(' [ NEWLINE ] [ params ] ')' [ ':' type ] do")  # type: ignore[no-redef]
    def def_expr(self, p: sly.yacc.YaccProduction):
        return terms.EDef(
            p.identifier.name,
            p.params or [],
            body=p.do,
            hint=terms.MaybeEHint(p.type or terms.MaybeEHintNothing()),
        )

    @_("params ',' [ NEWLINE ] param [ NEWLINE ]")
    def params(self, p: sly.yacc.YaccProduction):
        return p.params + [p.param]

    @_("param [ NEWLINE ]")  # type: ignore[no-redef]
    def params(self, p: sly.yacc.YaccProduction):
        return [p.param]

    @_("type_identifier")
    def type(self, p: sly.yacc.YaccProduction):
        return terms.EHint(p.type_identifier.name, [])

    @_("type_identifier '<' type { ',' type } '>'")  # type: ignore[no-redef]
    def type(self, p: sly.yacc.YaccProduction):
        return terms.EHint(p.type_identifier.name, concat(p.type0, p.type1))

    @_(
        "ENUM type_identifier '<' type_identifier { ',' type_identifier } '>' '{' [ NEWLINE ] [ variants ] '}'"
    )
    def enum(self, p: sly.yacc.YaccProduction):
        return terms.EEnumDeclaration(
            p.type_identifier0.name,
            variants=p.variants or [],
            generics=concat(p.type_identifier1, p.type_identifier2),
        )

    @_("variants variant [ NEWLINE ]")
    def variants(self, p: sly.yacc.YaccProduction):
        return p.variants + [p.variant]

    @_("variant [ NEWLINE ]")  # type: ignore[no-redef]
    def variants(self, p: sly.yacc.YaccProduction):
        return [p.variant]

    @_("ENUM type_identifier '{' [ NEWLINE ] [ variants ] '}'")  # type: ignore[no-redef]
    def enum(self, p: sly.yacc.YaccProduction):
        return terms.EEnumDeclaration(p.type_identifier.name, variants=p.variants or [])

    @_("TYPE_IDENTIFIER '(' type  { ',' type } ')'")
    def variant(self, p: sly.yacc.YaccProduction):
        return terms.EVariant(p.TYPE_IDENTIFIER, concat(p.type0, p.type1))

    @_("TYPE_IDENTIFIER")  # type: ignore[no-redef]
    def variant(self, p: sly.yacc.YaccProduction):
        return terms.EVariant(p.TYPE_IDENTIFIER)

    # @_("identifier { ',' identifier }")
    # def fields_unnamed(self, p:sly.yacc.YaccProduction):
    #     return concat(p.identifier0, p.identifier1)

    @_("identifier [ ':' type ]")
    def param(self, p: sly.yacc.YaccProduction):
        return terms.EParam(
            p.identifier.name, terms.MaybeEHint(p.type or terms.MaybeEHintNothing())
        )

    @_("IF expr THEN [ ':' type ] block_statement [ or_else ] END")
    def if_expr(self, p: sly.yacc.YaccProduction):
        return terms.EIf(
            p.expr,
            then=p.block_statement,
            or_else=terms.MaybeOrElse(p.or_else),
            hint=terms.MaybeEHint(p.type or terms.MaybeEHintNothing()),
        )

    @_("ELSE block_statement")
    def or_else(self, p: sly.yacc.YaccProduction):  # type: ignore[no-redef]
        return p.block_statement

    @_("ELIF expr THEN block_statement [ or_else ]")  # type: ignore[no-redef]
    def or_else(self, p: sly.yacc.YaccProduction):
        return terms.EIf(
            p.expr, then=p.block_statement, or_else=terms.MaybeOrElse(p.or_else)
        )

    @_("CASE expr OF [ NEWLINE ] [ cases ] END")
    def case_of(self, p: sly.yacc.YaccProduction):
        return terms.ECaseOf(p.expr, p.cases or [])

    @_("cases pattern do [ NEWLINE ]")
    def cases(self, p: sly.yacc.YaccProduction):
        return p.cases + [terms.ECase(p.pattern, p.do)]

    @_("pattern do [ NEWLINE ]")  # type: ignore[no-redef]
    def cases(self, p: sly.yacc.YaccProduction):
        return [terms.ECase(p.pattern, p.do)]

    # @_("clause { ',' clause } do")
    # def case(self, p:sly.yacc.YaccProduction):
    #     import operator

    #     return terms.ECase(
    #         functools.reduce(operator.__or__, concat(p.clause0, p.clause1)), p.do
    #     )

    # @_("identifier '=' pattern")
    # def clause(self, p:sly.yacc.YaccProduction):
    #     return {p.identifier.name: p.pattern}

    @_("match_as", "match_variant")  # , "tuple_pattern", "array_pattern"
    def pattern(self, p: sly.yacc.YaccProduction):
        return terms.EPattern(p[0])

    @_("identifier")
    def match_as(self, p: sly.yacc.YaccProduction):
        return terms.EMatchAs(p.identifier.name)

    # @_("'[' [ pattern ] { ',' pattern } ']'")
    # def array_pattern(self, p:sly.yacc.YaccProduction):
    #     return terms.EMatchArray(concat(p.pattern0, p.pattern1))

    # @_("'{' [ pattern ] { ',' pattern } '}'")
    # def tuple_pattern(self, p:sly.yacc.YaccProduction):
    #     return terms.EMatchTuple(concat(p.pattern0, p.pattern1))

    @_("TYPE_IDENTIFIER '(' [ NEWLINE ] [ patterns ] ')'")
    def match_variant(self, p: sly.yacc.YaccProduction):
        return terms.EMatchVariant(p.TYPE_IDENTIFIER, p.patterns or [])

    @_("TYPE_IDENTIFIER")  # type: ignore[no-redef]
    def match_variant(self, p: sly.yacc.YaccProduction):
        return terms.EMatchVariant(p.TYPE_IDENTIFIER, [])

    @_("patterns ',' [ NEWLINE ] pattern [ NEWLINE ]")
    def patterns(self, p: sly.yacc.YaccProduction):
        return p.patterns + [p.pattern]

    @_("pattern [ NEWLINE ]")  # type: ignore[no-redef]
    def patterns(self, p: sly.yacc.YaccProduction):
        return [p.pattern]

    @_("'[' [ NEWLINE ] [ exprs ] ']'")
    def array(self, p: sly.yacc.YaccProduction):
        return terms.EArray(p.exprs or [])

    # @_("'{' [ expr ] { ',' expr } '}'")
    # def tuple(self, p:sly.yacc.YaccProduction):
    #     return terms.ETuple(concat(p.expr0, p.expr1))

    @_("expr '(' [ NEWLINE ] [ exprs ] ')'")
    def call(self, p: sly.yacc.YaccProduction):
        return terms.ECall(p.expr, p.exprs or [])

    @_("TYPE_IDENTIFIER '(' [ NEWLINE ] [ exprs ] ')'")
    def variant_call(self, p: sly.yacc.YaccProduction):
        return terms.EVariantCall(p.TYPE_IDENTIFIER, p.exprs or [])

    @_("exprs ',' [ NEWLINE ] expr [ NEWLINE ]")
    def exprs(self, p: sly.yacc.YaccProduction):
        return p.exprs + [p.expr]

    @_("expr [ NEWLINE ]")  # type: ignore[no-redef]
    def exprs(self, p: sly.yacc.YaccProduction):
        return [p.expr]

    @_("IDENTIFIER")
    def identifier(self, p: sly.yacc.YaccProduction):
        return terms.EIdentifier(p.IDENTIFIER)

    @_("TYPE_IDENTIFIER")
    def type_identifier(self, p: sly.yacc.YaccProduction):
        return terms.ETypeIdentifier(p.TYPE_IDENTIFIER)

    @_("IDENTIFIER")
    def type_identifier(self, p: sly.yacc.YaccProduction):
        return terms.ETypeIdentifier(p.IDENTIFIER)

    @_("identifier [ ':' type ] '=' expr")
    def let(self, p):
        return terms.ELet(
            id=p.identifier.name,
            init=p.expr,
            hint=terms.MaybeEHint(p.type or terms.MaybeEHintNothing()),
        )

    @_("identifier ':' type_identifier '<' type { ',' type } MORE_OR_EQ expr")  # type: ignore[no-redef]
    def let(self, p):
        return terms.ELet(
            id=p.identifier.name,
            init=p.expr,
            hint=terms.MaybeEHint(
                terms.EHint(p.type_identifier.name, concat(p.type0, p.type1))
            ),
        )

    @_("INT")
    def int_literal(self, p: sly.yacc.YaccProduction) -> terms.ENumLiteral:
        return terms.ENumLiteral(float(p.INT.replace("_", "")))

    @_("FLOAT")
    def float_literal(self, p: sly.yacc.YaccProduction) -> terms.EFloatLiteral:
        return terms.EFloatLiteral(float(p.FLOAT.replace("_", "")))

    @_("STRING")
    def str_literal(self, p: sly.yacc.YaccProduction) -> terms.EStrLiteral:
        return terms.EStrLiteral(p.STRING[1:-1])
