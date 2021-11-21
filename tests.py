from sly import lex
import json

from typing import Generic
import pytest
from algorithm_j import Scheme, UnifyException, type_infer
from main import DEFAULT_CTX, AstEncoder, UwuLexer, UwuParser

import typed

from terms import *


@pytest.fixture
def parser():
    return UwuParser()


@pytest.fixture
def lexer():
    return UwuLexer()


def token(type, value, lineno, index):
    t = lex.Token()
    t.type = type
    t.value = value
    t.lineno = lineno
    t.index = index

    return t


# @pytest.mark.parametrize(
#     'program, expected_tokens', [
#         ("x:Option<Num>=None", [
#          token('IDENTIFIER', value='x', lineno=1, index=0),
#          token(type=':', value=':', lineno=1, index=1),
#          token(type='IDENTIFIER', value='Option', lineno=1, index=2),
#             token(type='<', value='<', lineno=1, index=8),
#             token(type='IDENTIFIER', value='Num', lineno=1, index=9),
#             token(type='>', value='>', lineno=1, index=15),
#             token(type='=', value='=', lineno=1, index=16),
#             token(type='IDENTIFIER', value='None', lineno=1, index=17),

#          ])
#     ])
# def test_tokenizer(program, expected_tokens, lexer):
#     tokens = [*lexer.tokenize(program)]
#     assert tokens == expected_tokens


@pytest.mark.parametrize(
    "program, ast",
    [
        ("1", [ELiteral("1", 1)]),
        ("'abc'", [ELiteral("'abc'", "abc")]),
        (
            "1+2*3",
            [
                EBinaryExpr(
                    "+",
                    ELiteral("1", 1),
                    EBinaryExpr("*", ELiteral("2", 2), ELiteral("3", 3)),
                )
            ],

        ),
        (
            "x=(2+3)*4",
            [
                EVariableDeclaration(
                    EIdentifier("x"),
                    EBinaryExpr(
                        "*",
                        EBinaryExpr("+", ELiteral("2", 2), ELiteral("3", 3)),
                        ELiteral("4", 4),
                    ),
                )
            ],

        ),
        # ("enum Option<value>{None\nSome(value)}\nx:Option<Num>=None"),
        (
            "def x(k) do k() end\ndef n() do 12 end\ny:Num=x(n)\nx",
            [
                EDef(
                    EIdentifier("x"),
                    [EParam(EIdentifier("k"))],
                    EDo([ECall(EIdentifier("k"), [])]),
                ),
                EDef(
                    EIdentifier("n"),
                    [],
                    EDo([ELiteral("12", 12)]),
                ),
                EVariableDeclaration(
                    EIdentifier("y"),
                    ECall(EIdentifier("x"), [EIdentifier("n")]),
                    hint=EHint(EIdentifier('Num'), []),
                ),
                EIdentifier("x"),
            ]
        ),
        # (
        #     "def flatMap(v, fn) do case v of None do None end Some(value) do fn(value) end end end",
        #     [
        #         Def(
        #             Identifier("flatMap"),
        #             [
        #                 Param(Identifier("v")),
        #                 Param(Identifier("fn")),
        #             ],
        #             Do(
        #                 [
        #                     CaseOf(
        #                         Identifier("v"),
        #                         [
        #                             Case(EnumPattern(Identifier("None"), []), Do([])),
        #                             Case(EnumPattern(Identifier("Some"), [
        #                                 EnumPattern(Identifier("value"), [])
        #                             ]), Do([])),
        #                         ],
        #                     )
        #                 ]
        #             ),
        #         )
        #     ],
        (
            "x=y=2+3",
            [
                EVariableDeclaration(
                    EIdentifier("x"),
                    EVariableDeclaration(
                        EIdentifier("y"),
                        EBinaryExpr("+", ELiteral("2", 2), ELiteral("3", 3)),
                    ),
                )
            ],

        ),
        (
            "do x = 1 end",
            [
                EDo(
                    [
                        EVariableDeclaration(
                            EIdentifier("x"),
                            ELiteral("1", 1),
                        )
                    ],
                )
            ],

        ),
        ("id('abc')", [
            ECall(EIdentifier("id"), [ELiteral("'abc'", "abc")])
        ], ),
        ("id(1)", [
            ECall(EIdentifier("id"), [ELiteral("1", 1)])
        ], ),
        ("id('12')\nid(1)", [ECall(EIdentifier("id"), [ELiteral("'12'", "12")]),
                             ECall(EIdentifier("id"), [ELiteral("1", 1)])
                             ], ),
        ("id(1+2)", [
            ECall(EIdentifier("id"), [
                EBinaryExpr("+", ELiteral("1", 1), ELiteral("2", 2))
            ])
        ], ),
        ("x:Option<Num>=None", [
            EVariableDeclaration(EIdentifier(
                'x'), EIdentifier('None'),
                hint=EHint(EIdentifier('Option'), [
                           EHint(EIdentifier('Num'), [])])
            )]),
        (
            "def add(a, b) do a + b end",
            [
                EDef(
                    identifier=EIdentifier(name="add"),
                    params=[EParam(EIdentifier("a")),
                            EParam(EIdentifier("b"))],
                    body=EDo(
                        body=[
                            EBinaryExpr(
                                op="+",
                                left=EIdentifier(name="a"),
                                right=EIdentifier(name="b"),
                            )
                        ],
                        hint=None,
                    ),
                    hint=None,
                ),
            ],
        ),
    ],
)
def test_parser(program, ast, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    assert program == EProgram(ast)


@ pytest.mark.parametrize(
    "program, expected_type",
    [
        ("1", typed.TNum()),
        ("Some(1)", typed.TGeneric('Option', [typed.TNum()])),
        ('id(id(1))', typed.TNum()),
        ("Some(Some(1))", typed.TGeneric('Option', [
         typed.TGeneric('Option', [typed.TNum()])])),
        (
            "1+2*3",
            typed.TNum(),
        ),
        (
            "x=(2+3)*4",
            typed.TNum(),
        ),
        # ("enum Option<value>{None\nSome(value)}\nx:Option<Num>=None"),
        (
            "def id2(a) do a end\nid2('12')",
            typed.TStr()
        ),
        (
            "def fun() do fun() + 1 end\nfun()",
            typed.TNum()
        ),
        ('def fun() do: Num 1 end\n fun()', typed.TNum()),
        (
            "def id2(a) do a end\nid2(1)\nid2('12')",
            typed.TStr()
        ),
        (
            "def id2(a) do a end\nid2('12')\nid2(1)",
            typed.TNum()
        ),
        #     "def flatMap(v, fn) do case v of None do None end Some(value) do fn(value) end end end",
        (
            "x=y=2+3",
            typed.TNum(),
        ),
        (
            "do x = 1 end",
            typed.TNum(),
        ),
        ("id('12')", typed.TStr()),
        ("id(1)",  typed.TNum()),
        ("id('12')\nid(1)",  typed.TNum()),
        ("x:Option<Num>=None", typed.TGeneric('Option', [typed.TNum()])),
        ("id(1+2)",  typed.TNum()),
        (
            "def add(a, b) do a + b end",
            typed.TDef([typed.TNum(), typed.TNum()],    typed.TNum(),),
        ),
        ("if 2 > 0 then: Option<Num> None else None end",
         typed.TGeneric('Option', [typed.TNum()])),
        ("if 2 > 0 then 1 else 2 end", typed.TNum()),
        ("if 2 > 0 then Some(Some(1)) end",
         typed.TGeneric('Option', [typed.TGeneric('Option', [typed.TNum()])])),
        ("if 2 > 0 then Some(1) elif 2 > 0 then Some(1) end",
         typed.TGeneric('Option', [typed.TNum()])),
        ("if 2 > 0 then Some(1) end",
         typed.TGeneric('Option',  [typed.TNum()])),
        ("if 2 > 0 then Some(1) elif 2 > 0 then None end", typed.TGeneric(
            'Option', [typed.TNum()])),
    ],
)
def test_infer(program, expected_type, parser, lexer):
    program = parser.parse(lexer.tokenize(program))

    assert type_infer(DEFAULT_CTX, program) == expected_type


@ pytest.mark.parametrize(
    "program",
    [
        (
            """x: Str = 134"""
        ),
        (
            "do: Str 1 end"
        ),
        (
            "def fun(): Str do 1 end"
        ),
        (
            "if 2 > 0 then: Num 1 else '12' end"
        ),
        (
            "if 2 > 0 then: Num '12' else 1 end"
        ),
        (
            "if 2 > 0 then: Num 1 elif 2 > 0 then '12' else 1 end"
        ),
        (
            "if 1+1 then 1 else 1 end"
        ),
        (
            "if 2 > 0 then: Str 1 else 2 end"
        ),
    ],
)
def test_do_expection(program, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    with pytest.raises(UnifyException):
        type_infer(DEFAULT_CTX, program)
