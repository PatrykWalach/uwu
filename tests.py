import json
import Annotate
from Unifier import unify
from typing import Generic
import pytest
from algorithm_w import Scheme, type_infer
from main import AstEncoder, UwuLexer, UwuParser, infer

import typed

from terms import *

from constraint import collect


@pytest.fixture
def parser():
    return UwuParser()


@pytest.fixture
def lexer():
    return UwuLexer()


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
        # ("enum Option<value>{None\nSome(value)}\nx:Option<number>=None"),
        (
            "def x(k) do k() end\ndef n() do 12 end\ny:number=x(n)\nx",
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
                    hint=typed.TNum(),
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


@pytest.mark.parametrize(
    "program, expected_type",
    [
        ("1", typed.TNum()),
        (
            "1+2*3",
            typed.TNum(),
        ),
        (
            "x=(2+3)*4",
            typed.TNum(),
        ),
        # ("enum Option<value>{None\nSome(value)}\nx:Option<number>=None"),
        (
            "def id2(a) do a end\nid2('12')",
            typed.TStr()
        ),
        (
            "def fun() do fun() + 1 end\nfun()",
            typed.TNum()
        ),
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
        ("id(1+2)",  typed.TNum()),
        (
            "def add(a, b) do a + b end",
            typed.TGeneric(  # Def<Params<number, number>, number>
                "Def",
                (
                    typed.TGeneric("Params", (typed.TNum(), typed.TNum())),
                    typed.TNum(),
                ),
            ),
        ),
    ],
)
def test_infer(program, expected_type, parser, lexer):
    program = parser.parse(lexer.tokenize(program))

    assert type_infer({
        'id': Scheme([-1], typed.TGeneric('Def', (typed.TGeneric('Params', (typed.TVar(-1),)), typed.TVar(-1)))),
    }, program) == expected_type


@pytest.mark.parametrize(
    "program, ast",
    [
        (
            """x: string = 134""",
            [EVariableDeclaration(EIdentifier(
                "x"), ELiteral("134", 134), typed.TStr())],
        ),
        (
            "do: string x = 1 end",
            [
                EDo(
                    [EVariableDeclaration(EIdentifier("x"), ELiteral("1", 1))],
                    typed.TStr(),
                )
            ],
        ),
        # (
        #     "do do x = 1 end\ny = x end",
        #     [
        #         Do(
        #             [
        #                 Do(
        #                     [
        #                         VariableDeclaration(
        #                             Identifier("x"), TypedLiteral("1", 1, typed.number())
        #                         )
        #                     ]
        #                 ),
        #                 VariableDeclaration(Identifier("y"), Identifier("x")),
        #             ]
        #         )
        #     ],
        # ),
    ],
)
def test_do_expection(program, ast, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    assert program == EProgram(ast)
    # with pytest.raises(VisitorTypeException):
    #     type_visitor(program)
