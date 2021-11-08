import pytest
from main import (
    UwuParser,
    UwuLexer,
    Program,
    Do,
    VariableDeclaration,
    Identifier,
    Literal,
    Type,
    VisitorTypeException,
    type_visitor,
)


@pytest.fixture
def parser():
    return UwuParser()


@pytest.fixture
def lexer():
    return UwuLexer()


def test_literal(parser, lexer):
    program = parser.parse(
        lexer.tokenize(
            """
            1
            """
        )
    )
    assert program == Program(
        [Literal("1", 1, Type(Identifier("number")))],
        None,
    )
    assert type_visitor(program) == Type(Identifier("number"))


def test_do(parser, lexer):
    program = parser.parse(
        lexer.tokenize(
            """
do
    x = 1
end"""
        )
    )
    assert program == Program(
        [
            Do(
                [
                    VariableDeclaration(
                        Identifier("x"),
                        Literal("1", 1, Type(Identifier("number"))),
                        None,
                    )
                ],
                None,
            )
        ],
        None,
    )
    assert type_visitor(program) == Type(Identifier("number"))


def test_variable_expection(parser, lexer):
    program = parser.parse(lexer.tokenize("""x: string = 1"""))
    assert program == Program(
        [
            VariableDeclaration(
                Identifier("x"),
                Literal("1", 1, Type(Identifier("number"))),
                Type(Identifier("string")),
            )
        ],
        None,
    )
    with pytest.raises(VisitorTypeException):
        type_visitor(program)


def test_do_expection(parser, lexer):
    program = parser.parse(
        lexer.tokenize(
            """
do: string
    x = 1
end"""
        )
    )
    assert program == Program(
        [
            Do(
                [
                    VariableDeclaration(
                        Identifier("x"),
                        Literal("1", 1, Type(Identifier("number"))),
                        None,
                    )
                ],
                Type(Identifier("string")),
            )
        ],
        None,
    )
    with pytest.raises(VisitorTypeException):
        type_visitor(program)
