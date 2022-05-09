from typing import Iterator

import pygments.token as t
from pygments.lexer import Lexer as PygmentsLexer
from sly import Lexer


class UwuLexerFull(Lexer):
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
        EXTERNAL,
        NOT_EQUAL,
        EQUAL,
        NEWLINE,
        WHITESPACE,
        COMMENT,
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
    EXTERNAL = r"`[^`]*`"

    COMMENT = r"\#.*"
    WHITESPACE = "[ \t]+"

    @_(r"\n([\s\t\n]|\#.*)*")
    def NEWLINE(self, t):
        self.lineno += t.value.count("\n")
        return t


def map_token(token) -> t._TokenType:
    match str(token):
        case "DEF" | "EXTERNAL":
            return t.Token.Keyword.Declaration
        case "DO" | "END" | "IF" | "ELSE" | "CASE" | "OF" | "ELIF" | "ENUM" | "ENUM" | "THEN":
            return t.Token.Keyword
        case "STRING":
            return t.Token.Literal.String.Single
        case "TYPE_IDENTIFIER":
            return t.Token.Keyword.Type
        case "NUMBER":
            return t.Token.Literal.Number
        case "IDENTIFIER":
            return t.Token.Name.Variable
        case "=" | "." | "[" | "]" | ":" | "+" | "-" | ">" | "<" | "*" | "/" | "|" | "%" "CONCAT" | "INT_DIV" | "NOT_EQUAL" | "EQUAL":
            return t.Token.Operator
        case "COMMENT":
            return t.Token.Comment.Single
        case "," | "{" | "}" | "(" | ")":
            return t.Token.Punctuation
        case "NEWLINE" | "WHITESPACE":
            return t.Token.Text.Whitespace
        case _:
            raise ValueError(f"Unknown token {token=}")


class CustomLexer(PygmentsLexer):
    def get_tokens_unprocessed(
        self, text: str
    ) -> Iterator[tuple[int, t._TokenType, str]]:
        for token in UwuLexerFull().tokenize(text):
            yield (token.index, map_token(token.type), token.value)
