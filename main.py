from __future__ import annotations

import ast
import dataclasses
import functools
import json
import logging
import operator
import random
import sys
import time
from functools import partial, reduce, wraps
from itertools import product
from os import terminal_size
from parser import UwuLexer, UwuParser
from subprocess import check_output
from typing import Any, Callable, Generic, Protocol, TypeAlias, TypeVar, Union, overload

from sly import Lexer, Parser
from watchdog.events import FileSystemEventHandler, PatternMatchingEventHandler
from watchdog.observers import Observer

import algorithm_j
import compile
import terms
import typed
from algorithm_j import Context, Scheme, fresh_ty_var, infer, type_infer


class AstEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            if obj.__dataclass_fields__:
                return {"__type": type(obj).__name__} | {
                    field: getattr(obj, field) for field in obj.__dataclass_fields__
                }
            return type(obj).__name__
        return json.JSONEncoder.default(self, obj)


BUILTINS: list[terms.Expr | terms.EEnumDeclaration] = [
    terms.EEnumDeclaration(
        "Option",
        [
            terms.EVariant("Some", [terms.EHint("VALUE", [])]),
            terms.EVariant("None", []),
        ],
        [terms.EIdentifier("VALUE")],
    ),
    terms.EEnumDeclaration(
        "Bool",
        [terms.EVariant("True", []), terms.EVariant("False", [])],
    ),
    terms.EDef("id", [terms.EParam("id")], terms.EDo([terms.EIdentifier("id")])),
    terms.ELet("unit", terms.EExternal("undefined"), terms.EHint("Unit")),
]

DEFAULT_CTX: Context = {
    "Str": Scheme([], typed.TStr()),
    "Num": Scheme([], typed.TNum()),
    "Unit": Scheme([], typed.TUnit()),
    "Callable": Scheme([], typed.TCallableCon()),
    "Array": Scheme([], typed.TArrayCon()),
}

for builitin in BUILTINS:
    type_infer(DEFAULT_CTX, builitin)


def main():
    lexer = UwuLexer()
    parser = UwuParser()

    src_path = "examples/index.uwu"

    with open(src_path, "r") as f:
        data = f.read()

    ast = parser.parse(lexer.tokenize(data))

    if ast == None:
        logging.error("Failed to parse")
        return

    ast = terms.EProgram([*BUILTINS, ast])

    logging.info("Parsed")

    try:
        type_infer(
            DEFAULT_CTX,
            ast,
        )
    except Exception as e:
        logging.exception(e)
        return

    try:
        algorithm_j.is_exhaustive({}, ast)
    except Exception as e:
        logging.exception(e)
        return

    logging.info("Inferred")

    js = compile.compile(ast)
    logging.info("Compiled")

    path = src_path + ".js"
    with open(path, "w") as f:
        f.write(js)

    logging.info("Written")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
    main()
