from sly import Parser, Lexer
import dataclasses


class UwuLexer(Lexer):
    tokens = {NUMBER, STRING, IDENTIFIER, DEF, DO, END, IF, ELSE, CASE, OF, SPREAD,CONCAT
,INT_DIV}
    literals = {"=", ".", "[", "]", ",", "{", "}", "(", ")", "%", "+", "-", ">", "<"}
    DEF = r"def"
    DO = r"do"
    END = r"end"
    IF = r"if"
    ELSE = r"else"
    CASE = r"case"
    OF = r"of"
    SPREAD = r"\.{3}"
    STRING = r"'[^(\\')]*?'"
    NUMBER = r"\d+"
    IDENTIFIER = r"\w+"
    CONCAT =r"\+{2}"
    INT_DIV = r"/{2}"


@dataclasses.dataclass(frozen=True)
class Do:
    pass


class UwuParser(Parser):
    tokens = UwuLexer.tokens
    debugfile = "parser.out"

    @_("exprs")
    def program(self, p):
        return

    @_("exprs exprs", "expr")
    def exprs(self, p):
        return

    @_(
        "do",
        "identifier",
        "literal",
        "_def",
        "_if",
        "call",
        "case",
        "variable_declaration",
        "binary_expr",
    )
    def expr(self, p):
        return

    @_(
        "expr CONCAT expr",
        "expr '+' expr",
        "expr '-' expr",
        "expr '/' expr",
        "expr INT_DIV expr",
    )
    def binary_expr(self, p):
        return

    @_("o_type DO exprs END")
    def do(self, p):
        return

    @_("DEF IDENTIFIER '(' params ')' do")
    def _def(self, p):
        return

    @_("'%' IDENTIFIER", "")
    def o_type(self, p):
        return

    @_("params ',' params", "o_type identifier")
    def params(self, p):
        return

    @_("IF expr do", "IF expr DO exprs ELSE exprs END")
    def _if(self, p):
        return

    @_("CASE expr OF cases END")
    def case(self, p):
        return

    @_("cases cases", "patterns do")
    def cases(self, p):
        return

    @_(
        "patterns ',' patterns",
        "identifier",
        "identifier '(' patterns ')'",
        "list_pattern",
        "array_pattern",
    )
    def patterns(self, p):
        return

    @_(
        "'[' patterns ',' SPREAD identifier ']'",
        "'[' patterns ',' SPREAD identifier ',' patterns ']'",
        "'[' SPREAD identifier ',' patterns ']'",
        "'[' patterns ']'",
        "'[' ']'",
    )
    def array_pattern(self, p):
        return

    @_(
        "'{' patterns ',' SPREAD identifier '}'",
        "'{' patterns '}'",
        "'{' '}'",
    )
    def list_pattern(self, p):
        return

    @_("callee '(' arguments ')'")
    def call(self, p):
        return

    @_("expr", "arguments ',' arguments")
    def arguments(self, p):
        return

    @_("identifier")
    def callee(self, p):
        return

    @_("IDENTIFIER")
    def identifier(self, p):
        return

    @_("identifier '=' expr")
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

    observer = Observer()
    observer.schedule(Handler(), path=sys.argv[1], recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
