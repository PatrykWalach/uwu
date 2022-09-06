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
from algorithm_j import NonExhaustiveMatchException, fresh_ty_var, type_infer
import Ctx

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
                terms.EParam("a", hint=terms.EMaybeHint((a))),
                terms.EParam("b", hint=terms.EMaybeHint((b))),
            ],
            terms.EDo(terms.EBlock([terms.EExpr(terms.EExternal(ext))])),
            terms.EMaybeHint((ret)),
            generics=list(map(terms.EIdentifier, generics)),
        )
    )

v = fresh_ty_var()

Builtin = terms.EProgram(
    [

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
            terms.EMaybeHint ** terms.EHint(typed.TUnit.id),
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
        SimpleBinaryOpDef(
            "+.", "a+b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id
        ),
        SimpleBinaryOpDef(
            "/.", "a/b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id
        ),
        SimpleBinaryOpDef(
            "*.", "a*b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id
        ),
        SimpleBinaryOpDef(
            "**.", "a**b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id
        ),
        SimpleBinaryOpDef(
            "-.", "a-b", typed.TFloat.id, typed.TFloat.id, typed.TFloat.id
        ),
        # float eq
        SimpleBinaryOpDef(
            "<.", "a<b", typed.TFloat.id, typed.TFloat.id, typed.TBool.id
        ),
        SimpleBinaryOpDef(
            ">.", "a>b", typed.TFloat.id, typed.TFloat.id, typed.TBool.id
        ),
        SimpleBinaryOpDef(
            ">=.", "a>=b", typed.TFloat.id, typed.TFloat.id, typed.TBool.id
        ),
        SimpleBinaryOpDef(
            "<=.", "a<=b", typed.TFloat.id, typed.TFloat.id, typed.TBool.id
        ),
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
        SimpleBinaryOpDef(
            "and", "a&&b", typed.TBool.id, typed.TBool.id, typed.TBool.id
        ),
        SimpleBinaryOpDef(
            "||",
            "a||b",
            generics=["A"],
            a="A",
            b="A",
            ret="A",
        ),
        SimpleBinaryOpDef("or", "a||b", typed.TBool.id, typed.TBool.id, typed.TBool.id),
    ],
    {
        typed.TNum.id: Ctx.Scheme([], typed.TNum),
        "Int": Ctx.Scheme([], typed.TNum),
        typed.TStr.id: Ctx.Scheme([], typed.TStr),
        typed.TFloat.id: Ctx.Scheme([], typed.TFloat),
        typed.TUnit.id: Ctx.Scheme([], typed.TUnit),
        typed.TRegex.id: Ctx.Scheme([], typed.TRegex),
        typed.TCallable.id: Ctx.Scheme([], typed.TCallable),
        typed.TArrayCon.id: Ctx.Scheme([], typed.TArrayCon),
        # Bool
        typed.TBool.id: Ctx.Scheme([], typed.TBool),
        f"${typed.TrueCon.id}": Ctx.Scheme([], typed.TrueCon),
        f"${typed.FalseCon.id}": Ctx.Scheme([], typed.FalseCon),
        f"{typed.TrueCon.id}": Ctx.Scheme([], typed.TDef(typed.TrueCon, typed.TBool)),
        f"{typed.FalseCon.id}": Ctx.Scheme([], typed.TDef(typed.FalseCon, typed.TBool)),
        # Option
        typed.TOptionCon.id: Ctx.Scheme([], typed.TOptionCon),
        f"${typed.SomeCon.id}": Ctx.Scheme([], typed.SomeCon),
        f"${typed.NoneCon.id}": Ctx.Scheme([], typed.NoneCon),
        typed.SomeCon.id: Ctx.Scheme([v.id], typed.TDef(typed.TAp( typed.SomeCon, v), typed.TOption(v))),
        typed.NoneCon.id: Ctx.Scheme([v.id], typed.TDef(typed.NoneCon, typed.TOption(v))),
    },
)



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

        ast = Builtin + ast

        logging.info(f"Parsed {src_path}")

        try:
            type_infer(
                {},
                ast,
            )
        except NonExhaustiveMatchException as e:
            logging.warning(e)
        except Exception as e:
            logging.exception(e)
            return

        logging.info(f"Inferred {src_path}")

        ast = ast.fold_with(compile.Hoister()).fold_with(compile.DefCleaner()).fold_with(compile.UnnestDo())
        js = compile.compile(ast)

        logging.info(f"Compiled {src_path}")

        path = src_path + ".js"
        with open(path, "w") as f:
            f.write(js)

        logging.info(f"Written {src_path}")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
    main()
