import json
from dataclasses import dataclass
from pathlib import WindowsPath
from subprocess import check_output
from typing import Generic

import pytest
from sly import lex

import algorithm_j
import typed
from compile import Hoist, compile
from main import BUILTINS, DEFAULT_CTX, AstEncoder, UwuLexer, UwuParser
from terms import *


@pytest.fixture
def parser():
    return UwuParser()


@pytest.fixture
def lexer():
    return UwuLexer()


@pytest.mark.parametrize(
    "program, ast",
    (
        [
            ("1", [EExpr << ELiteral(1)]),
            ("'abc'", [EExpr << ELiteral("abc")]),
            (
                "-2+2",
                [
                    EExpr
                    << EBinaryExpr(
                        "+",
                        EExpr << EUnaryExpr("-", EExpr << ELiteral(2)),
                        EExpr << ELiteral(2),
                    )
                ],
            ),
            (
                "-(2+2)",
                [
                    EExpr
                    << EUnaryExpr(
                        "-",
                        EExpr
                        << EBinaryExpr("+", EExpr << ELiteral(2), EExpr << ELiteral(2)),
                    )
                ],
            ),
            (
                "x=2\n-1",
                [
                    EExpr << ELet("x", EExpr << ELiteral(2)),
                    EExpr << EUnaryExpr("-", EExpr << ELiteral(1)),
                ],
            ),
            (
                "x=2-1",
                [
                    EExpr
                    << ELet(
                        "x",
                        EExpr
                        << EBinaryExpr("-", EExpr << ELiteral(2), EExpr << ELiteral(1)),
                    )
                ],
            ),
            (
                "Some(2)",
                [EExpr << EVariantCall("Some", [EExpr << ELiteral(2)])],
            ),
            (
                "Some(2)(2)",
                [
                    EExpr
                    << ECall(
                        EExpr << EVariantCall("Some", [EExpr << ELiteral(2)]),
                        [EExpr << ELiteral(2)],
                    )
                ],
            ),
            (
                "Some(2)\n(2)",
                [
                    EExpr << EVariantCall("Some", [EExpr << ELiteral(2)]),
                    EExpr << ELiteral(2),
                ],
            ),
            (
                "x=id(2)",
                [
                    EExpr
                    << ELet(
                        "x",
                        EExpr
                        << ECall(EExpr << EIdentifier("id"), [EExpr << ELiteral(2)]),
                    )
                ],
            ),
            (
                "(x=id)(2)",
                [
                    EExpr
                    << ECall(
                        EExpr << ELet("x", EExpr << EIdentifier("id")),
                        [EExpr << ELiteral(2)],
                    )
                ],
            ),
            (
                "x=id\n(2)",
                [EExpr << ELet("x", EExpr << EIdentifier("id")), EExpr << ELiteral(2)],
            ),
            (
                "1+2*3",
                [
                    EExpr
                    << EBinaryExpr(
                        "+",
                        EExpr << ELiteral(1),
                        EExpr
                        << EBinaryExpr("*", EExpr << ELiteral(2), EExpr << ELiteral(3)),
                    )
                ],
            ),
            (
                "x=(2+3)*4",
                [
                    EExpr
                    << ELet(
                        "x",
                        EExpr
                        << EBinaryExpr(
                            "*",
                            EExpr
                            << EBinaryExpr(
                                "+", EExpr << ELiteral(2), EExpr << ELiteral(3)
                            ),
                            EExpr << ELiteral(4),
                        ),
                    )
                ],
            ),
            (
                "enum StrOrNum{String(Str)\nNumber(Num)}\nx=Number(1)\nx=String('12')",
                [
                    EExpr
                    << EEnumDeclaration(
                        id="StrOrNum",
                        variants=[
                            EVariant(id="String", fields=[EHint(id="Str")]),
                            EVariant(id="Number", fields=[EHint(id="Num")]),
                        ],
                    ),
                    EExpr
                    << ELet(
                        id="x",
                        init=EExpr
                        << EVariantCall(
                            callee="Number", args=[EExpr << ELiteral(value=1.0)]
                        ),
                    ),
                    EExpr
                    << ELet(
                        id="x",
                        init=EExpr
                        << EVariantCall(
                            callee="String", args=[EExpr << ELiteral(value="12")]
                        ),
                    ),
                ],
            ),
            (
                "def x(k) do k() end\ndef n() do 12 end\ny:Num=x(n)\nx",
                [
                    EExpr
                    << EDef(
                        "x",
                        [EParam("k")],
                        EDo(EBlock([EExpr << ECall(EExpr << EIdentifier("k"))])),
                    ),
                    EExpr << EDef("n", [], EDo(EBlock([EExpr << ELiteral(12)]))),
                    EExpr
                    << ELet(
                        "y",
                        EExpr
                        << ECall(
                            EExpr << EIdentifier("x"), [EExpr << EIdentifier("n")]
                        ),
                        hint=MaybeEHint(EHint("Num")),
                    ),
                    EExpr << EIdentifier("x"),
                ],
            ),
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
            (
                "x=y=2+3",
                [
                    EExpr
                    << ELet(
                        "x",
                        EExpr
                        << ELet(
                            "y",
                            EExpr
                            << EBinaryExpr(
                                "+", EExpr << ELiteral(2), EExpr << ELiteral(3)
                            ),
                        ),
                    )
                ],
            ),
            (
                "do x = 1 end",
                [
                    EExpr
                    << EDo(
                        EBlock(
                            [EExpr << ELet("x", EExpr << ELiteral(1))],
                        )
                    )
                ],
            ),
            (
                "id('abc')",
                [
                    EExpr
                    << ECall(EExpr << EIdentifier("id"), [EExpr << ELiteral("abc")])
                ],
            ),
            (
                "id(1)",
                [EExpr << ECall(EExpr << EIdentifier("id"), [EExpr << ELiteral(1)])],
            ),
            (
                "id('12')\nid(1)",
                [
                    EExpr
                    << ECall(EExpr << EIdentifier("id"), [EExpr << ELiteral("12")]),
                    EExpr << ECall(EExpr << EIdentifier("id"), [EExpr << ELiteral(1)]),
                ],
            ),
            (
                "id(1+2)",
                [
                    EExpr
                    << ECall(
                        EExpr << EIdentifier("id"),
                        [
                            EExpr
                            << EBinaryExpr(
                                "+", EExpr << ELiteral(1), EExpr << ELiteral(2)
                            )
                        ],
                    )
                ],
            ),
            (
                "x:Option<Num>=None()",
                [
                    EExpr
                    << ELet(
                        "x",
                        EExpr << EVariantCall("None"),
                        hint=MaybeEHint(
                            EHint("Option", [EHint("Num")]),
                        ),
                    )
                ],
            ),
            (
                "def add(a, b) do a + b end",
                [
                    EExpr
                    << EDef(
                        identifier="add",
                        params=[EParam("a"), EParam("b")],
                        body=EDo(
                            block=EBlock(
                                [
                                    EExpr
                                    << EBinaryExpr(
                                        op="+",
                                        left=EExpr << EIdentifier(name="a"),
                                        right=EExpr << EIdentifier(name="b"),
                                    )
                                ],
                            )
                        ),
                    ),
                ],
            ),
            (
                "enum AOrB {A B}",
                [
                    EExpr
                    << EEnumDeclaration(
                        id="AOrB",
                        variants=[
                            EVariant(id="A"),
                            EVariant(id="B"),
                        ],
                    )
                ],
            ),
            (
                "case x of Some(value) do 2 end None() do 3 end end",
                [
                    EExpr
                    << ECaseOf(
                        EExpr << EIdentifier(name="x"),
                        [
                            ECase(
                                EPattern
                                << EMatchVariant(
                                    id="Some",
                                    patterns=[EPattern << EMatchAs("value")],
                                ),
                                EDo(EBlock([EExpr << ELiteral(value=2.0)])),
                            ),
                            ECase(
                                EPattern << EMatchVariant("None"),
                                EDo(EBlock([EExpr << ELiteral(value=3.0)])),
                            ),
                        ],
                    )
                ],
            ),
            ("\n\n", []),
            ("\nid\n", [EExpr << EIdentifier("id")]),
            (
                "case x of\n\nend",
                [EExpr << ECaseOf(EExpr << EIdentifier("x"), [])],
            ),
            (
                "case x of\nSome() do end\nend",
                [
                    EExpr
                    << ECaseOf(
                        EExpr << EIdentifier("x"),
                        [ECase(EPattern << EMatchVariant("Some"))],
                    )
                ],
            ),
            (
                "case x of Some(a,\nb,\nc\n) do end end",
                [
                    EExpr
                    << ECaseOf(
                        EExpr << EIdentifier("x"),
                        [
                            ECase(
                                EPattern
                                << EMatchVariant(
                                    "Some",
                                    [
                                        EPattern << EMatchAs("a"),
                                        EPattern << EMatchAs("b"),
                                        EPattern << EMatchAs("c"),
                                    ],
                                )
                            )
                        ],
                    )
                ],
            ),
            (
                "case x of Some(a\n,b\n,c\n) do end end",
                [
                    EExpr
                    << ECaseOf(
                        EExpr << EIdentifier("x"),
                        [
                            ECase(
                                EPattern
                                << EMatchVariant(
                                    "Some",
                                    [
                                        EPattern << EMatchAs("a"),
                                        EPattern << EMatchAs("b"),
                                        EPattern << EMatchAs("c"),
                                    ],
                                )
                            )
                        ],
                    )
                ],
            ),
            ("do\n\nend", [EExpr << EDo()]),
            ("do\nid\nend", [EExpr << EDo(EBlock([EExpr << EIdentifier("id")]))]),
            (
                "f(a\n,b\n,c\n)",
                [
                    EExpr
                    << ECall(
                        EExpr << EIdentifier("f"),
                        [
                            EExpr << EIdentifier("a"),
                            EExpr << EIdentifier("b"),
                            EExpr << EIdentifier("c"),
                        ],
                    )
                ],
            ),
            (
                "f(a,\nb,\nc\n)",
                [
                    EExpr
                    << ECall(
                        EExpr << EIdentifier("f"),
                        [
                            EExpr << EIdentifier("a"),
                            EExpr << EIdentifier("b"),
                            EExpr << EIdentifier("c"),
                        ],
                    )
                ],
            ),
            (
                "F(a\n,b\n,c\n)",
                [
                    EExpr
                    << EVariantCall(
                        "F",
                        [
                            EExpr << EIdentifier("a"),
                            EExpr << EIdentifier("b"),
                            EExpr << EIdentifier("c"),
                        ],
                    )
                ],
            ),
            (
                "F(a,\nb,\nc\n)",
                [
                    EExpr
                    << EVariantCall(
                        "F",
                        [
                            EExpr << EIdentifier("a"),
                            EExpr << EIdentifier("b"),
                            EExpr << EIdentifier("c"),
                        ],
                    )
                ],
            ),
            (
                "[a\n,b\n,c\n]",
                [
                    EExpr
                    << EArray(
                        [
                            EExpr << EIdentifier("a"),
                            EExpr << EIdentifier("b"),
                            EExpr << EIdentifier("c"),
                        ]
                    )
                ],
            ),
            (
                "[a,\nb,\nc\n]",
                [
                    EExpr
                    << EArray(
                        [
                            EExpr << EIdentifier("a"),
                            EExpr << EIdentifier("b"),
                            EExpr << EIdentifier("c"),
                        ]
                    )
                ],
            ),
            ("None()", [EExpr << EVariantCall("None")]),
            (
                "def x() do\ny\n\n#comment\n\nend",
                [EExpr << EDef("x", [], EDo(EBlock([EExpr << EIdentifier("y")])))],
            ),
            # (
            #     "case [Some(1), None()] of [Some(value), None()] do value end end",
            #     [
            #         EExpr<<ECaseOf(
            #             EArray(
            #                 [
            #                     EExpr<<ECall(EExpr<<EIdentifier("Some"), [EExpr<<ELiteral("1", 1.0)]),
            #                     EExpr<<ECall(EExpr<<EIdentifier("None"), []),
            #                 ]
            #             ),
            #             cases=[
            #                 ECase(
            #                     pattern=EMatchArray(
            #                         patterns=[
            #                             EEnumPattern(
            #                                 id=EExpr<<EIdentifier(name="Some"),
            #                                 patterns=[
            #                                     EPattern<<EMatchAs(
            #                                         identifier=EExpr<<EIdentifier(name="value")
            #                                     )
            #                                 ],
            #                             ),
            #                             EEnumPattern(
            #                                 id=EExpr<<EIdentifier(name="None"), patterns=[]
            #                             ),
            #                         ],
            #                     ),
            #                     body=EExpr<<EDo(body=[EExpr<<EIdentifier(name="value")]),
            #                 )
            #             ],
            #         )
            #     ],
            # ),
            # (
            #     "case [Some(1), None()] of [] do 4 end end",
            #     [
            #         EExpr<<ECaseOf(
            #             EArray(
            #                 [
            #                     EExpr<<ECall(EExpr<<EIdentifier("Some"), [EExpr<<ELiteral("1", 1)]),
            #                     EExpr<<ECall(EExpr<<EIdentifier("None"), []),
            #                 ]
            #             ),
            #             [
            #                 ECase(
            #                     pattern=EMatchArray(patterns=[]),
            #                     body=EExpr<<EDo(body=[EExpr<<ELiteral(raw="4", value=4.0)]),
            #                 )
            #             ],
            #         )
            #     ],
            # ),
            # (
            #     "case [Some(1), None()] of arr do 5 end end",
            #     [
            #         EExpr<<ECaseOf(
            #             EArray(
            #                 [
            #                     EExpr<<ECall(EExpr<<EIdentifier("Some"), [EExpr<<ELiteral("1", 1.0)]),
            #                     EExpr<<ECall(EExpr<<EIdentifier("None")),
            #                 ]
            #             ),
            #             [
            #                 ECase(
            #                     patterns={"$": EPattern<<EMatchAs(identifier="arr")},
            #                     body=EExpr<<EDo(body=[EExpr<<ELiteral(raw="5", value=5.0)]),
            #                 )
            #             ],
            #         )
            #     ],
            # ),
        ]
    ),
)
def test_parser(program, ast, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    assert program == EProgram(ast)


@pytest.mark.parametrize(
    "program, expected_type",
    [
        ("1", typed.TNum()),
        ("x=1\nx", typed.TNum()),
        ("x=1\na=x\na", typed.TNum()),
        ("x=1\na=x", typed.TNum()),
        ("Some(1)", typed.TOption(typed.TNum())),
        ("id(id(1))", typed.TNum()),
        ("2+id(1)", typed.TNum()),
        ("Some(Some(1))", typed.TOption(typed.TOption(typed.TNum()))),
        (
            "1+2*3",
            typed.TNum(),
        ),
        (
            "x=(2+3)*4",
            typed.TNum(),
        ),
        # ("enum Option<value>{None\nSome(value)}\nx:Option<Num>=None"),
        ("def id2(a) do a end\nid2(12)\nid2('12')", typed.TStr()),
        ("def id2<T>(a:T):T do a end\nid2(12)\nid2('12')", typed.TStr()),
        pytest.param(
            "def fun() do fun() + 1 end\nfun()",
            typed.TNum(),
            marks=pytest.mark.skip(reason="TODO: fix recursion"),
        ),
        ("def fun() do: Num 1 end\n fun()", typed.TNum()),
        ("def id2(a) do a end\nid2(1)\nid2('12')", typed.TStr()),
        ("def id2(a) do a end\nid2('12')\nid2(1)", typed.TNum()),
        ("x=Some(1)\nx:Option<Str>=None()", typed.TOption(typed.TStr())),
        (
            "x=y=2+3",
            typed.TNum(),
        ),
        (
            "do x=1 end",
            typed.TNum(),
        ),
        ("id('12')", typed.TStr()),
        ("id(1)", typed.TNum()),
        ("id('12')\nid(1)", typed.TNum()),
        ("x:Option<Num>=None()", typed.TOption(typed.TNum())),
        ("id(1+2)", typed.TNum()),
        (
            "def add(a, b) do a + b end",
            typed.TDef(typed.TNum(), typed.TDef(typed.TNum(), typed.TNum())),
        ),
        ("if 2 > 0 then 1 else 2 end", typed.TNum()),
        (
            "if 2 > 0 then Some(Some(1)) else None() end",
            typed.TOption(typed.TOption(typed.TNum())),
        ),
        (
            "if 2 > 0 then Some(1) elif 2 > 0 then Some(1) else None() end",
            typed.TOption(typed.TNum()),
        ),
        ("if 2 > 0 then Some(1) else None() end", typed.TOption(typed.TNum())),
        (
            "if 2 > 0 then Some(1) elif 2 > 0 then None() else None() end",
            typed.TOption(typed.TNum()),
        ),
        ("enum AB{A B}\nx:AB=A()", typed.TCon("AB", typed.KStar(), ["A", "B"])),
        (
            "enum ABC<X,Y,Z> {A(X)B(Y)C(Z)}\nx:ABC<Num,Num,Num>=A(1)",
            typed.TAp(
                typed.TAp(
                    typed.TAp(
                        typed.TCon(
                            "ABC",
                            typed.KFun(
                                typed.KStar(),
                                typed.KFun(
                                    typed.KStar(),
                                    typed.KFun(typed.KStar(), typed.KStar()),
                                ),
                            ),
                            ["A", "B", "C"],
                        ),
                        typed.TNum(),
                    ),
                    typed.TNum(),
                ),
                typed.TNum(),
            ),
        ),
        (
            "x=Some(1)\ncase x of Some(value) do 2 end None() do 3 end end",
            typed.TNum(),
        ),
        (
            "def flatMap(v, fn) do case v of None() do None() end Some(value) do fn(value) end end end\ndef some(value) do Some(value) end\nflatMap(Some(1),some)",
            typed.TOption(typed.TNum()),
        ),
        ("[Some(1), None()]", typed.TArray(typed.TOption(typed.TNum()))),
        # (
        #     "case [Some(1), None()] of [Some(value), None()] do 2 end [None(), Some(value)] do 3 end [] do 4 end arr do 5 end end",
        #     typed.TNum(),
        # ),
        # (
        #     "case [Some(1), None()] of [Some(value), None()] do [Some(value)] end [None(), Some(value)] do [Some(value)] end [] do [] end arr do arr end end",
        #     typed.TArray(typed.TOption(typed.TNum())),
        # ),
        (
            "enum Point<X,Y,Z>{Point2D(X,Y) Point3D(X,Y,Z)}\nPoint3D(1,'2',True())",
            typed.TAp(
                typed.TAp(
                    typed.TAp(
                        typed.TCon(
                            "Point",
                            typed.KFun(
                                typed.KStar(),
                                typed.KFun(
                                    typed.KStar(),
                                    typed.KFun(typed.KStar(), typed.KStar()),
                                ),
                            ),
                            ["Point2D", "Point3D"],
                        ),
                        typed.TNum(),
                    ),
                    typed.TStr(),
                ),
                typed.TBool(),
            ),
        ),
        ("do end", typed.TUnit()),
        (
            "enum StrOrNum{String(Str)\nNumber(Num)}\nx=Number(1)\nx=String('12')",
            typed.TCon("StrOrNum", typed.KStar(), ["String", "Number"]),
        ),
        (
            "enum TupleType<A, B>{Tuple(A, B)}\ncase Tuple(Some(1), Some(2)) of Tuple(None(), _) do 2 end Tuple(_, None()) do 3 end Tuple(Some(a), Some(b)) do a + b end end",
            typed.TNum(),
        ),
        (
            "enum TupleType<A, B>{Tuple(A, B)}\ncase Tuple(Some(1), Some(2)) of Tuple(None(), Some(a)) do a end Tuple(None(), None()) do 3 end Tuple(_, None()) do 3 end Tuple(Some(a), Some(b)) do a + b end end",
            typed.TNum(),
        ),
        # ("{1,'2'}", typed.TTuple([typed.TNum(), typed.TStr()])),
    ],
)
def test_infer(program, expected_type, parser, lexer):
    program = parser.parse(lexer.tokenize(program))

    assert algorithm_j.type_infer(DEFAULT_CTX, program) == expected_type


@pytest.mark.parametrize(
    "id, program, expected_output",
    (
        (
            [
                ("0", "`console.log`(1)", "1"),
                ("1", "x=1\n`console.log`(x)", "1"),
                ("2", "x=1\na = x\n`console.log`(a)", "1"),
                ("3", "x=1\n`console.log`(a = x)", "1"),
                ("4", "`console.log`(1+2*3)", "7"),
                ("5", "`console.log`(x=(2+3)*4)", "20"),
                ("6", "`console.log`(if 2 > 0 then 1 else 2 end)", "1"),
                ("7", "`console.log`(if 2 < 0 then 1 else 2 end)", "2"),
                (
                    "8",
                    "`console.log`(case Some(1) of Some(_) do 2 end None() do 3 end end)",
                    "2",
                ),
                (
                    "9",
                    "`console.log`(case Some(1) of Some(value) do 1 end None() do 3 end end)",
                    "1",
                ),
                (
                    "10",
                    "enum ABC<X,Y,Z> {A(X) B(Y) C(Z)}\n`console.log`(case A(1) of A(a) do a end B(b) do b end C(c) do c end end)",
                    "1",
                ),
                (
                    "11",
                    "`console.log`(case Some(Some(1)) of Some(Some(value)) do value end None() do 2 end Some() do 3 end end)",
                    "1",
                ),
                (
                    "12",
                    "`console.log`(case None() of Some(Some(value)) do value end None() do 2 end Some() do 3 end end)",
                    "2",
                ),
                (
                    "13",
                    "`console.log`(case Some(None()) of Some(Some(value)) do value end None() do 2 end Some() do 3 end end)",
                    "3",
                ),
                (
                    "14",
                    "enum PairType<A,B> {Pair(A,B)}\n`console.log`(case Pair(1,2) of Pair(x, y) do x end end)",
                    "1",
                ),
                (
                    "15",
                    "enum PairType<A,B> {Pair(A,B)}\n`console.log`(case Pair(1,2) of Pair(x, y) do y end end)",
                    "2",
                ),
                (
                    "16",
                    "enum PairType<A,B> {Pair(A,B)}\n`console.log`(case Pair(1,2) of Pair(a) do a end end)",
                    "1",
                ),
                (
                    "17",
                    "enum PairType<A,B> {Pair(A,B)}\n`console.log`(case Pair(1,Pair(2,3)) of Pair(x, Pair(y, z)) do z end Pair(c, v) do c end end)",
                    "3",
                ),
                # (
                #     "`console.log`(case [Some(1), None()] of [Some(value), None()] do value end [None(), Some(value)] do 3 end [] do 4 end arr do 5 end end)",
                #     "1",
                # ),
                # (
                #     "`console.log`(case [] of [Some(value), None()] do 2 end [None(), Some(value)] do 3 end [] do 4 end arr do 5 end end)",
                #     "4",
                # ),
                # (
                #     "`console.log`(case [None(), Some(1)] of [Some(value), None()] do 2 end [None(), Some(value)] do 3 end [] do 4 end arr do 5 end end)",
                #     "3",
                # ),
                # (
                #     "`console.log`(case [Some(1), Some(1), None()] of [Some(value), None()] do 2 end [None(), Some(value)] do 3 end [] do 4 end arr do 5 end end)",
                #     "5",
                # ),
                (
                    "22",
                    "def add(a, b) do a + b end\naddTwo=add(2)\n`console.log`(addTwo(3))",
                    "5",
                ),
                (
                    "23",
                    "def add(a) do def add(b) do a + b end end\naddTwo=add(2)\n`console.log`(addTwo(3))",
                    "5",
                ),
                ("24", "def add(a, b) do a + b end\n`console.log`(add(2,3))", "5"),
                (
                    "25",
                    "def add(a) do def add(b) do a + b end end\n`console.log`(add(2,3))",
                    "5",
                ),
                ("26", "def zero() do 0 end\n`console.log`(zero())", "0"),
                (
                    "27",
                    "def partial(fn, arg) do def thunk() do fn(arg) end end\npartial(`console.log`,0)()",
                    "0",
                ),
                ("28", "def zero() do 0 end\n`console.log`(zero(unit))", "0"),
                (
                    "29",
                    "def partial(fn, arg) do def thunk() do fn(arg) end end\npartial(`console.log`,0,unit)",
                    "0",
                ),
                ("30", "`console.log`(do end)", "undefined"),
                # ("31", "`console.log`(case {1,2} of {x,_} do x end end)", "1"),
                # ("32", "`console.log`(case {1,2} of {_,y} do y end end)", "2"),
                ("33", "`console.log`(if 2*2 != 4 then 0 else 1 end)", "1"),
                ("37", "`console.log`(if 2*2 == 4 then 0 else 1 end)", "0"),
                ("34", "`console.log`('a'++'b')", "ab"),
                ("35", "`console.log`([1]|[2])", "[ 1, 2 ]"),
                ("36", "`console.log`(-2+2)", "0"),
            ]
        )
    ),
)
def test_compile_with_snapshot(id, program, expected_output, snapshot, parser, lexer):
    id = id + ".js"
    program = parser.parse(lexer.tokenize(program))
    snapshot.snapshot_dir = "snapshots"
    ast = EProgram([*BUILTINS, *program.body])
    snapshot.assert_match(compile(ast.fold_with(Hoist())), id)
    # path: WindowsPath = snapshot.snapshot_dir
    assert check_output(
        ["node", snapshot.snapshot_dir / id]
    ) == f"{expected_output}\n".encode("UTF-8")


@pytest.mark.parametrize(
    "program, exception",
    [
        ("x: Str = 134", algorithm_j.UnifyException),
        ("do: Str 1 end", algorithm_j.UnifyException),
        ("def fun(): Str do 1 end", algorithm_j.UnifyException),
        ("if 2 > 0 then: Num 1 else '12' end", algorithm_j.UnifyException),
        ("if 2 > 0 then: Num '12' else 1 end", algorithm_j.UnifyException),
        (
            "if 2 > 0 then: Num 1 elif 2 > 0 then '12' else 1 end",
            algorithm_j.UnifyException,
        ),
        ("if 1+1 then 1 else 1 end", algorithm_j.UnifyException),
        ("if 2 > 0 then: Str 1 else 2 end", algorithm_j.UnifyException),
        (
            "enum TupleType<A,B>{Tuple(A,B)}\ncase Tuple(None(), Some(32)) of\nTuple(_, None()) do 5 end\nTuple(Some(a), Some(b)) do\na+b\nend\nend",
            algorithm_j.NonExhaustiveMatchException,
        ),
        (
            "enum TupleType<A,B>{Tuple(A,B)}\ncase Tuple(None(), Some(32)) of\nTuple(None(), None()) do 5 end\nTuple(Some(a), Some(b)) do\na+b\nend\nend",
            algorithm_j.NonExhaustiveMatchException,
        ),
        (
            "case Some(None()) of\nSome(None()) do 5 end\nNone() do\n6\nend\nend",
            algorithm_j.NonExhaustiveMatchException,
        ),
        (
            "case Some(None()) of\nSome(Some(a)) do a end\nNone() do\n6\nend\nend",
            algorithm_j.NonExhaustiveMatchException,
        ),
        (
            "case Some(None()) of\nSome(Some(a)) do a end\nSome(None()) do\n6\nend\nend",
            algorithm_j.NonExhaustiveMatchException,
        ),
    ],
)
def test_do_expection(program, parser, lexer, exception):
    program = parser.parse(lexer.tokenize(program))
    with pytest.raises(exception):
        algorithm_j.type_infer(DEFAULT_CTX, program)
