from sly import Parser, Lexer
import dataclasses


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
        TYPE_IDENTIFIER,
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
    }
    DEF = r"def"
    DO = r"do"
    END = r"end"
    IF = r"if"
    ELSE = r"else"
    ELIF = r"elif"
    CASE = r"case"
    ENUM = r"enum"
    STRUCT = r"struct"
    OF = r"of"
    SPREAD = r"\.{3}"
    STRING = r"'[^(\\')]*?'"
    NUMBER = r"\d+"
    IDENTIFIER = r"[a-z_]\w*"
    TYPE_IDENTIFIER = r"[A-Z]\w*"
    CONCAT = r"\+{2}"
    INT_DIV = r"/{2}"
    ignore_comment = r"#.*\n"

    ignore = " \t"

    @_(r"\n+")
    def ignore_newline(self, t):
        self.lineno += len(t.value)


@dataclasses.dataclass(frozen=True)
class Do:
    pass


class UwuParser(Parser):
    tokens = UwuLexer.tokens
    debugfile = "parser.out"

    @_("{ _program }")
    def program(self, p):
        return

    @_("expr", "struct", "enum")
    def _program(self, p):
        return

    precedence = (
        ("left", CONCAT),
        ("left", "+", "-"),
        ("left", "*", "/", INT_DIV),
        ("right", "UMINUS"),
    )

    @_(
        "do",
        "identifier",
        "literal",
        "_def",
        "_if",
        "call",
        "case_of",
        "variable_declaration",
        "binary_expr",
        "array",
        "tuple",
        "'-' expr %prec UMINUS",
        "'(' expr ')'",
    )
    def expr(self, p):
        return

    @_(
        "expr CONCAT expr",
        "expr '+' expr",
        "expr '-' expr",
        "expr '/' expr",
        "expr '*' expr",
        "expr INT_DIV expr",
    )
    def binary_expr(self, p):
        return

    @_(
        "DO [ type ] { expr } END",
    )
    def do(self, p):
        return

    @_("DEF identifier '(' [ param ] { ',' param } ')' [ type ] do")
    def _def(self, p):
        return

    @_("':' type_identifier [ '<' identifier { ',' identifier } '>' ]")
    def type(self, p):
        return

    @_(
        "STRUCT type_identifier [ '<' identifier { ',' identifier } '>' ] '{' { identifier type } '}'"
    )
    def struct(self, p):
        return

    @_(
        "ENUM type_identifier [ '<' identifier { ',' identifier } '>' ] '{' { enum_key } '}'"
    )
    def enum(self, p):
        return

    @_("identifier [ '(' identifier { ',' identifier } ')' ]")
    def enum_key(self, p):
        return

    @_("identifier [ type ]")
    def param(self, p):
        return

    @_("IF expr DO { expr } { _elif } [ ELSE { expr } ] END")
    def _if(self, p):
        return

    @_("ELIF expr DO { expr }")
    def _elif(self, p):
        return

    @_("CASE expr OF case { case } END")
    def case_of(self, p):
        return

    @_("pattern { ',' pattern } do")
    def case(self, p):
        return

    @_(
        "enum_pattern",
        "tuple_pattern",
        "array_pattern",
    )
    def pattern(self, p):
        return

    @_("'[' { pattern ',' } [ SPREAD identifier { ',' pattern } ] ']'")
    def array_pattern(self, p):
        return

    @_("type_identifier [ '(' pattern { ',' pattern } ')' ]")
    def enum_pattern(self, p):
        return

    @_("'{' { pattern ',' } [ SPREAD identifier { ',' pattern } ] '}'")
    def tuple_pattern(self, p):
        return

    @_("'[' [ expr ] { ',' expr } ']'")
    def array(self, p):
        return

    @_("'{' [ expr ] { ',' expr } '}'")
    def tuple(self, p):
        return

    @_("callee '(' [ expr ]  { ',' expr } ')'")
    def call(self, p):
        return

    @_("identifier")
    def callee(self, p):
        return

    @_("IDENTIFIER")
    def identifier(self, p):
        return

    @_("TYPE_IDENTIFIER")
    def type_identifier(self, p):
        return

    @_("identifier [ type ] '=' expr")
    def variable_declaration(self, p):
        return

    @_("STRING", "NUMBER")
    def literal(self, p):
        return


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

if __name__ == "__main__":
    lexer = UwuLexer()
    parser = UwuParser()

    with open("test.uwu", "r") as f:
        data = f.read()

    ast = parser.parse(lexer.tokenize(data))
