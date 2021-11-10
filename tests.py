from typing import Generic
import pytest
from main import UwuLexer, UwuParser, infer

import typed

from terms import *
from Annotate import Annotate
from constraint import collect


@pytest.fixture
def parser():
    return UwuParser()


@pytest.fixture
def lexer():
    return UwuLexer()


@pytest.mark.parametrize(
    "program, ast, expected_type",
    [
        ("1", [Literal("1", 1)], typed.number()),
        (
            "1+2*3",
            [
                BinaryExpr(
                    "+",
                    Literal("1", 1),
                    BinaryExpr("*", Literal("2", 2), Literal("3", 3)),
                )
            ],
            typed.number(),
        ),
        (
            "x=(2+3)*4",
            [
                VariableDeclaration(
                    Identifier("x"),
                    BinaryExpr(
                        "*",
                        BinaryExpr("+", Literal("2", 2), Literal("3", 3)),
                        Literal("4", 4),
                    ),
                )
            ],
            typed.number(),
        ),
        # ("enum Option<value>{None\nSome(value)}\nx:Option<number>=None"),
        (
            "def x(k) do k() end\ndef n() do 12 end\ny:number=x(n)\nx",
            [
                Def(
                    Identifier("x"),
                    [Param(Identifier("k"))],
                    Do([Call(Identifier("k"), [])]),
                ),
                Def(
                    Identifier("n"),
                    [],
                    Do([Literal("12", 12)]),
                ),
                VariableDeclaration(
                    Identifier("y"),
                    Call(Identifier("x"), [Identifier("n")]),
                    hint=typed.number(),
                ),
                Identifier("x"),
            ],
            typed.GenericType(
                "Def",
                (
                    typed.GenericType(
                        "Params",
                        (
                            typed.GenericType(
                                "Def",
                                (
                                    typed.GenericType("Params", tuple()),
                                    typed.Var(0),
                                ),
                            ),
                        ),
                    ),
                    typed.Var(0),
                ),
            ),
        ),
        # f: Def<Var(0), Def<Def<Var(0), Var(1)>, Var(1)>>
        #
        # x = f(12, n -> n + 1)
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
        #     typed.GenericType(
        #         "Def",
        #         (
        #             typed.GenericType(
        #                 "Params",
        #                 (
        #                     typed.GenericType("Option", (typed.Var(0),)),
        #                     typed.GenericType(
        #                         "Def",
        #                         (
        #                             typed.GenericType("Params", (typed.Var(0),)),
        #                             typed.GenericType("Option", (typed.Var(1),)),
        #                         ),
        #                     ),
        #                 ),
        #             ),
        #             typed.GenericType("Option", (typed.Var(1),)),
        #         ),
        #     ),
        # ),
        (
            "x=y=2+3",
            [
                VariableDeclaration(
                    Identifier("x"),
                    VariableDeclaration(
                        Identifier("y"),
                        BinaryExpr("+", Literal("2", 2), Literal("3", 3)),
                    ),
                )
            ],
            typed.number(),
        ),
        (
            "do x = 1 end",
            [
                Do(
                    [
                        VariableDeclaration(
                            Identifier("x"),
                            Literal("1", 1),
                        )
                    ],
                )
            ],
            typed.number(),
        ),
        (
            "def add(a, b) do a + b end",
            [
                Def(
                    identifier=Identifier(name="add"),
                    params=[Param(Identifier("a")), Param(Identifier("b"))],
                    body=Do(
                        body=[
                            BinaryExpr(
                                op="+",
                                left=Identifier(name="a"),
                                right=Identifier(name="b"),
                            )
                        ],
                        hint=None,
                    ),
                    hint=None,
                ),
            ],
            typed.GenericType(  # Def<Params<number, number>, number>
                "Def",
                (
                    typed.GenericType("Params", (typed.number(), typed.number())),
                    typed.number(),
                ),
            ),
        ),
    ],
)
def test_do(program, ast, expected_type, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    assert program == Program(ast)



    assert infer(program) == expected_type




from Unifier import unify


@pytest.mark.parametrize(
    "program, ast",
    [
        (
            """x: string = 134""",
            [VariableDeclaration(Identifier("x"), Literal("134", 134), typed.string())],
        ),
        (
            "do: string x = 1 end",
            [
                Do(
                    [VariableDeclaration(Identifier("x"), Literal("1", 1))],
                    typed.string(),
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
    assert program == Program(ast)
    # with pytest.raises(VisitorTypeException):
    #     type_visitor(program)
