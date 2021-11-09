from typing import Generic
import pytest
from main import UwuLexer, UwuParser

from typed import Var, number, string
from typed_terms import (
    TypedProgram,
    TypedDo,
    TypedIdentifier,
    TypedLiteral,
    TypedVariableDeclaration,
)
from terms import BinaryExpr, Do, Identifier, Program, VariableDeclaration,Literal
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
        ("1", [Literal("1", 1)], number()),
        (
            "1+2*3",
            [
                BinaryExpr(
                    "+",
                    Literal("1", 1),
                    BinaryExpr("*", Literal("2", 2), Literal("3", 3)),
                )
            ],
            number()
        ),
        (
            """do
x = 1
end""",
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
            number(),
        ),
    ],
)
def test_do(program, ast, expected_type, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    assert program == Program(ast)

    typed_term = Annotate({})(program)
    constraints = collect(typed_term)
    subst = unify(constraints)

    assert subst.apply_type(typed_term.type) == expected_type


from Unifier import unify


@pytest.mark.parametrize(
    "program, ast",
    [
        (
            """x: string = 134""",
            [
                TypedVariableDeclaration(
                    Identifier("x"), Literal("134", 134), string()
                )
            ],
        ),
        (
            """do: string
            x = 1
            end""",
            [
                TypedDo(
                    [
                        VariableDeclaration(
                            Identifier("x"), Literal("1", 1)
                        )
                    ],
                    string(),
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
        #                             Identifier("x"), TypedLiteral("1", 1, number())
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
