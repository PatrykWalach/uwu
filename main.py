from __future__ import annotations

import dataclasses
import glob
import json
import logging
import sys
from parser import UwuLexer, UwuParser

import algorithm_j
import compile
import terms
import typed
from algorithm_j import Context, NonExhaustiveMatchException, Scheme, type_infer


class AstEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            if obj.__dataclass_fields__:
                return {"__type": type(obj).__name__} | {
                    field: getattr(obj, field) for field in obj.__dataclass_fields__
                }
            return type(obj).__name__
        return json.JSONEncoder.default(self, obj)


BUILTINS: list[terms.EExpr] = [
    terms.EExpr
    ** terms.EEnumDeclaration(
        "Option",
        variants=[
            terms.EVariant("Some", [terms.EHint("VALUE")]),
            terms.EVariant("None"),
        ],
        generics=[terms.EIdentifier("VALUE")],
    ),
    terms.EExpr
    ** terms.EEnumDeclaration(
        "Bool",
        variants=[terms.EVariant("True"), terms.EVariant("False")],
    ),
    terms.EExpr
    ** terms.EDef(
        "id",
        [terms.EParam("id")],
        terms.EDo ** terms.EBlock([terms.EExpr ** terms.EIdentifier("id")]),
    ),
    terms.EExpr
    ** terms.ELet(
        "unit",
        terms.EExpr ** terms.EExternal("undefined"),
        terms.MaybeEHint ** terms.EHint("Unit"),
    ),
]

DEFAULT_CTX: Context = {
    "Str": Scheme([], typed.TStr),
    "Num": Scheme([], typed.TNum),
    "Unit": Scheme([], typed.TUnit),
    "Callable": Scheme([], typed.TCallableCon),
    "Array": Scheme([], typed.TArrayCon),
}


for builitin in BUILTINS:
    type_infer(DEFAULT_CTX, builitin)


def main():
    lexer = UwuLexer()
    parser = UwuParser()

    match sys.argv:
        case [_, arg]:
            pattern = arg
        case _:
            pattern = "**/*.uwu"

    for src_path in glob.glob(pattern):

        with open(src_path, "r") as f:
            data = f.read()

        ast = parser.parse(lexer.tokenize(data))

        if not isinstance(ast, terms.EProgram):
            logging.error(f"Failed {src_path} to parse")
            return

        ast = terms.EProgram([*BUILTINS, *ast.body])

        logging.info(f"Parsed {src_path}")

        try:
            type_infer(
                DEFAULT_CTX,
                ast,
            )
        except NonExhaustiveMatchException as e:
            logging.warning(e)
        except Exception as e:
            logging.exception(e)
            return

        logging.info(f"Inferred {src_path}")

        ast = ast.fold_with(compile.Hoist())
        js = compile.compile(ast)

        logging.info(f"Compiled {src_path}")

        path = src_path + ".js"
        with open(path, "w") as f:
            f.write(js)

        logging.info(f"Written {src_path}")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
    main()
