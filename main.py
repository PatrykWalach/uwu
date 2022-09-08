from __future__ import annotations

import builtins
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
from algorithm_j import (
    Context,
    NonExhaustiveMatchException,
    Scheme,
    fresh_ty_var,
    type_infer,
)


class AstEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            if obj.__dataclass_fields__:
                return {"__type": type(obj).__name__} | {
                    field: getattr(obj, field) for field in obj.__dataclass_fields__
                }
            return type(obj).__name__
        return json.JSONEncoder.default(self, obj)


def SimpleBinaryOpDef(
    op: terms.BinaryOp, ext: str, a: str, b: str, ret: str, generics: list[str] = []
):
    return BinaryOpDef(
        op, ext, terms.EHint(a), terms.EHint(b), terms.EHint(ret), generics=generics
    )


def BinaryOpDef(
    op: terms.BinaryOp,
    ext: str,
    a: terms.EHint,
    b: terms.EHint,
    ret: terms.EHint,
    generics: list[str] = [],
):
    return terms.EExpr(
        terms.EBinaryOpDef(
            op,
            [
                terms.EParam("a", hint=terms.MaybeEHint((a))),
                terms.EParam("b", hint=terms.MaybeEHint((b))),
            ],
            terms.EDo(terms.EBlock([terms.EExpr(terms.EExternal(ext))])),
            terms.MaybeEHint((ret)),
            generics=list(map(terms.EIdentifier, generics)),
        )
    )


BUILTINS: list[terms.EExpr] = [
    terms.EExpr
    ** terms.EDef(
        "id",
        [terms.EParam("x")],
        terms.EDo ** terms.EBlock([terms.EExpr ** terms.EIdentifier("x")]),
    ),
    terms.EExpr
    ** terms.ELet(
        "unit",
        terms.EExpr ** terms.EExternal("undefined"),
        terms.MaybeEHint ** terms.EHint("Unit"),
    ),
    # int
    SimpleBinaryOpDef("+", "a+b", typed.TNum.id, typed.TNum.id, typed.TNum.id),
    SimpleBinaryOpDef(
        "/", "Math.floor(a/b)", typed.TNum.id, typed.TNum.id, typed.TNum.id
    ),
    SimpleBinaryOpDef("*", "a*b", typed.TNum.id, typed.TNum.id, typed.TNum.id),
    SimpleBinaryOpDef("**", "a**b", typed.TNum.id, typed.TNum.id, typed.TNum.id),
    SimpleBinaryOpDef("-", "a-b", typed.TNum.id, typed.TNum.id, typed.TNum.id),
    # int eq
    SimpleBinaryOpDef("<", "a<b", typed.TNum.id, typed.TNum.id, typed.TBool.id),
    SimpleBinaryOpDef(">", "a>b", typed.TNum.id, typed.TNum.id, typed.TBool.id),
    SimpleBinaryOpDef(">=", "a>=b", typed.TNum.id, typed.TNum.id, typed.TBool.id),
    SimpleBinaryOpDef("<=", "a<=b", typed.TNum.id, typed.TNum.id, typed.TBool.id),
    # float
    SimpleBinaryOpDef("+.", "a+b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id),
    SimpleBinaryOpDef("/.", "a/b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id),
    SimpleBinaryOpDef("*.", "a*b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id),
    SimpleBinaryOpDef("**.", "a**b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id),
    SimpleBinaryOpDef("-.", "a-b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id),
    # float eq
    SimpleBinaryOpDef("<.", "a<b", typed.TFloat.id, typed.TFloat.id, typed.TBool.id),
    SimpleBinaryOpDef(">.", "a>b", typed.TFloat.id, typed.TFloat.id, typed.TBool.id),
    SimpleBinaryOpDef(">=.", "a>=b", typed.TFloat.id, typed.TFloat.id, typed.TBool.id),
    SimpleBinaryOpDef("<=.", "a<=b", typed.TFloat.id, typed.TFloat.id, typed.TBool.id),
    # str
    SimpleBinaryOpDef("<>", "a+b", typed.TStr.id, typed.TStr.id, typed.TStr.id),
    SimpleBinaryOpDef(
        "=~", "b.test(a)", typed.TStr.id, typed.TRegex.id, typed.TBool.id
    ),
    # eq
    SimpleBinaryOpDef(
        "==",
        "Object.is(a,b)",
        ("A"),
        ("A"),
        (typed.TBool.id),
        generics=[("A")],
    ),
    SimpleBinaryOpDef(
        "!=",
        "!Object.is(a,b)",
        ("A"),
        ("A"),
        (typed.TBool.id),
        generics=[("A")],
    ),
    # array
    BinaryOpDef(
        "++",
        "a.concat(b)",
        terms.EHint(typed.TArrayCon.id, [terms.EHint("A")]),
        terms.EHint(typed.TArrayCon.id, [terms.EHint("A")]),
        terms.EHint(typed.TArrayCon.id, [terms.EHint("A")]),
        generics=[("A")],
    ),
    # bool
    SimpleBinaryOpDef(
        "&&",
        "a&&b",
        generics=["A"],
        a="A",
        b="A",
        ret="A",
    ),
    SimpleBinaryOpDef("and", "a&&b", typed.TBool.id, typed.TBool.id, typed.TBool.id),
    SimpleBinaryOpDef(
        "||",
        "a||b",
        generics=["A"],
        a="A",
        b="A",
        ret="A",
    ),
    SimpleBinaryOpDef("or", "a||b", typed.TBool.id, typed.TBool.id, typed.TBool.id),
]

v = fresh_ty_var()


DEFAULT_CTX = Context(
    {},
    {
        typed.TStr.id: Scheme([], typed.TStr),
        typed.TNum.id: Scheme([], typed.TNum),
        "Int": Scheme([], typed.TNum),
        typed.TFloat.id: Scheme([], typed.TFloat),
        typed.TUnit.id: Scheme([], typed.TUnit),
        typed.TRegex.id: Scheme([], typed.TRegex),
        typed.TCallableCon.id: Scheme([], typed.TCallableCon),
        typed.TArrayCon.id: Scheme([], typed.TArrayCon),
        # Bool
        typed.TBool.id: Scheme([], typed.TBool),
        f"${typed.TrueCon.id}": Scheme([], typed.TrueCon),
        f"${typed.FalseCon.id}": Scheme([], typed.FalseCon),
        f"{typed.TrueCon.id}": Scheme([], typed.TDef(typed.TrueCon, typed.TBool)),
        f"{typed.FalseCon.id}": Scheme([], typed.TDef(typed.FalseCon, typed.TBool)),
        # Option
        typed.TOptionCon.id: Scheme([], typed.TOptionCon),
        f"${typed.SomeCon.id}": Scheme([], typed.SomeCon),
        f"${typed.NoneCon.id}": Scheme([], typed.NoneCon),
        typed.SomeCon.id: Scheme(
            [v.id], typed.TDef(typed.TAp(typed.SomeCon, v), typed.TOption(v))
        ),
        typed.NoneCon.id: Scheme([v.id], typed.TDef(typed.NoneCon, typed.TOption(v))),
    },
)


for builitin in BUILTINS:
    type_infer(DEFAULT_CTX, builitin)


def green(text: str) -> str:
    return "\033[92m{}\033[00m".format(text)


def yellow(text: str) -> str:
    return "\033[93m{}\033[00m".format(text)


def print(s: str, end: str = ""):
    builtins.print(f"\r{s}", end=end, flush=True)


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

        print(f"{yellow('Parsing')} {src_path}")

        ast = parser.parse(lexer.tokenize(data))

        if not isinstance(ast, terms.EProgram):
            print(f"Failed parse")
            return

        ast = terms.EProgram([*BUILTINS, *ast.body])

        print(f"{green('Parsed')} {src_path}")

        try:
            type_infer(
                DEFAULT_CTX,
                ast,
            )
        except NonExhaustiveMatchException as e:
            print(e)
        except Exception as e:
            print(e)
            return

        print(f"{green('Inferred')} {src_path}")

        ast = ast.fold_with(compile.Hoister()).fold_with(compile.DefCleaner())
        js = compile.compile(ast)

        print(f"{green('Compiled')} {src_path}")

        path = src_path + ".js"
        with open(path, "w") as f:
            f.write(js)

        print(f"{green('Compiled')} {src_path} to {(path)}", end="\n")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
    main()
