import json
from dataclasses import dataclass
from pathlib import WindowsPath
from subprocess import check_output
from typing import Generic

import pytest
from sly import lex

import algorithm_j
import typed
from compile import compile
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
    [
        ("1", [ELiteral(1)]),
        ("'abc'", [ELiteral("abc")]),
        ("-2+2", [EBinaryExpr("+", EUnaryExpr("-", ELiteral(2)), ELiteral(2))]),
        ("-(2+2)", [EUnaryExpr("-", EBinaryExpr("+", ELiteral(2), ELiteral(2)))]),
        ("x=2\n-1", [ELet("x", ELiteral(2)), EUnaryExpr("-", ELiteral(1))]),
        ("x=2-1", [ELet("x", EBinaryExpr("-", ELiteral(2), ELiteral(1)))]),
        (
            "Some(2)",
            [EVariantCall("Some", [ELiteral(2)])],
        ),
        (
            "Some(2)(2)",
            [ECall(EVariantCall("Some", [ELiteral(2)]), [ELiteral(2)])],
        ),
        (
            "Some(2)\n(2)",
            [EVariantCall("Some", [ELiteral(2)]), ELiteral(2)],
        ),
        (
            "x=id(2)",
            [ELet("x", ECall(EIdentifier("id"), [ELiteral(2)]))],
        ),
        (
            "(x=id)(2)",
            [ECall(ELet("x", EIdentifier("id")), [ELiteral(2)])],
        ),
        (
            "x=id\n(2)",
            [ELet("x", EIdentifier("id")), ELiteral(2)],
        ),
        (
            "1+2*3",
            [
                EBinaryExpr(
                    "+",
                    ELiteral(1),
                    EBinaryExpr("*", ELiteral(2), ELiteral(3)),
                )
            ],
        ),
        (
            "x=(2+3)*4",
            [
                ELet(
                    "x",
                    EBinaryExpr(
                        "*",
                        EBinaryExpr("+", ELiteral(2), ELiteral(3)),
                        ELiteral(4),
                    ),
                )
            ],
        ),
        (
            "enum StrOrNum{String(Str)\nNumber(Num)}\nx=Number(1)\nx=String('12')",
            [
                EEnumDeclaration(
                    id="StrOrNum",
                    variants=[
                        EVariant(id="String", fields=[EHint(id="Str")]),
                        EVariant(id="Number", fields=[EHint(id="Num")]),
                    ],
                ),
                ELet(
                    id="x",
                    init=EVariantCall(callee="Number", args=[ELiteral(value=1.0)]),
                ),
                ELet(
                    id="x",
                    init=EVariantCall(callee="String", args=[ELiteral(value="12")]),
                ),
            ],
        ),
        (
            "def x(k) do k() end\ndef n() do 12 end\ny:Num=x(n)\nx",
            [
                EDef("x", [EParam("k")], EDo([ECall(EIdentifier("k"))])),
                EDef("n", [], EDo([ELiteral(12)])),
                ELet(
                    "y",
                    ECall(EIdentifier("x"), [EIdentifier("n")]),
                    hint=EHint("Num"),
                ),
                EIdentifier("x"),
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
            [ELet("x", ELet("y", EBinaryExpr("+", ELiteral(2), ELiteral(3))))],
        ),
        (
            "do x = 1 end",
            [
                EDo(
                    [ELet("x", ELiteral(1))],
                )
            ],
        ),
        (
            "id('abc')",
            [ECall(EIdentifier("id"), [ELiteral("abc")])],
        ),
        (
            "id(1)",
            [ECall(EIdentifier("id"), [ELiteral(1)])],
        ),
        (
            "id('12')\nid(1)",
            [
                ECall(EIdentifier("id"), [ELiteral("12")]),
                ECall(EIdentifier("id"), [ELiteral(1)]),
            ],
        ),
        (
            "id(1+2)",
            [
                ECall(
                    EIdentifier("id"),
                    [EBinaryExpr("+", ELiteral(1), ELiteral(2))],
                )
            ],
        ),
        (
            "x:Option<Num>=None()",
            [
                ELet(
                    "x",
                    EVariantCall("None"),
                    hint=EHint("Option", [EHint("Num")]),
                )
            ],
        ),
        (
            "def add(a, b) do a + b end",
            [
                EDef(
                    identifier="add",
                    params=[EParam("a"), EParam("b")],
                    body=EDo(
                        body=[
                            EBinaryExpr(
                                op="+",
                                left=EIdentifier(name="a"),
                                right=EIdentifier(name="b"),
                            )
                        ],
                    ),
                ),
            ],
        ),
        (
            "enum AOrB {A B}",
            [
                EEnumDeclaration(
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
                ECaseOf(
                    EIdentifier(name="x"),
                    [
                        ECase(
                            EMatchVariant(
                                id="Some",
                                patterns=[EMatchAs("value")],
                            ),
                            EDo([ELiteral(value=2.0)]),
                        ),
                        ECase(
                            EMatchVariant("None"),
                            EDo([ELiteral(value=3.0)]),
                        ),
                    ],
                )
            ],
        ),
        ("\n\n", []),
        ("\nid\n", [EIdentifier("id")]),
        (
            "case x of\n\nend",
            [ECaseOf(EIdentifier("x"), [])],
        ),
        (
            "case x of\nSome() do end\nend",
            [ECaseOf(EIdentifier("x"), [ECase(EMatchVariant("Some"))])],
        ),
        (
            "case x of Some(a,\nb,\nc\n) do end end",
            [
                ECaseOf(
                    EIdentifier("x"),
                    [
                        ECase(
                            EMatchVariant(
                                "Some",
                                [EMatchAs("a"), EMatchAs("b"), EMatchAs("c")],
                            )
                        )
                    ],
                )
            ],
        ),
        (
            "case x of Some(a\n,b\n,c\n) do end end",
            [
                ECaseOf(
                    EIdentifier("x"),
                    [
                        ECase(
                            EMatchVariant(
                                "Some",
                                [EMatchAs("a"), EMatchAs("b"), EMatchAs("c")],
                            )
                        )
                    ],
                )
            ],
        ),
        ("do\n\nend", [EDo()]),
        ("do\nid\nend", [EDo([EIdentifier("id")])]),
        (
            "f(a\n,b\n,c\n)",
            [
                ECall(
                    EIdentifier("f"),
                    [EIdentifier("a"), EIdentifier("b"), EIdentifier("c")],
                )
            ],
        ),
        (
            "f(a,\nb,\nc\n)",
            [
                ECall(
                    EIdentifier("f"),
                    [EIdentifier("a"), EIdentifier("b"), EIdentifier("c")],
                )
            ],
        ),
        (
            "F(a\n,b\n,c\n)",
            [EVariantCall("F", [EIdentifier("a"), EIdentifier("b"), EIdentifier("c")])],
        ),
        (
            "F(a,\nb,\nc\n)",
            [EVariantCall("F", [EIdentifier("a"), EIdentifier("b"), EIdentifier("c")])],
        ),
        (
            "[a\n,b\n,c\n]",
            [EArray([EIdentifier("a"), EIdentifier("b"), EIdentifier("c")])],
        ),
        (
            "[a,\nb,\nc\n]",
            [EArray([EIdentifier("a"), EIdentifier("b"), EIdentifier("c")])],
        ),
        ("None()", [EVariantCall("None")]),
        ("def x() do\ny\n\n#comment\n\nend", [EDef("x", [], EDo([EIdentifier("y")]))]),
        # (
        #     "case [Some(1), None()] of [Some(value), None()] do value end end",
        #     [
        #         ECaseOf(
        #             EArray(
        #                 [
        #                     ECall(EIdentifier("Some"), [ELiteral("1", 1.0)]),
        #                     ECall(EIdentifier("None"), []),
        #                 ]
        #             ),
        #             cases=[
        #                 ECase(
        #                     pattern=EMatchArray(
        #                         patterns=[
        #                             EEnumPattern(
        #                                 id=EIdentifier(name="Some"),
        #                                 patterns=[
        #                                     EMatchAs(
        #                                         identifier=EIdentifier(name="value")
        #                                     )
        #                                 ],
        #                             ),
        #                             EEnumPattern(
        #                                 id=EIdentifier(name="None"), patterns=[]
        #                             ),
        #                         ],
        #                     ),
        #                     body=EDo(body=[EIdentifier(name="value")]),
        #                 )
        #             ],
        #         )
        #     ],
        # ),
        # (
        #     "case [Some(1), None()] of [] do 4 end end",
        #     [
        #         ECaseOf(
        #             EArray(
        #                 [
        #                     ECall(EIdentifier("Some"), [ELiteral("1", 1)]),
        #                     ECall(EIdentifier("None"), []),
        #                 ]
        #             ),
        #             [
        #                 ECase(
        #                     pattern=EMatchArray(patterns=[]),
        #                     body=EDo(body=[ELiteral(raw="4", value=4.0)]),
        #                 )
        #             ],
        #         )
        #     ],
        # ),
        # (
        #     "case [Some(1), None()] of arr do 5 end end",
        #     [
        #         ECaseOf(
        #             EArray(
        #                 [
        #                     ECall(EIdentifier("Some"), [ELiteral("1", 1.0)]),
        #                     ECall(EIdentifier("None")),
        #                 ]
        #             ),
        #             [
        #                 ECase(
        #                     patterns={"$": EMatchAs(identifier="arr")},
        #                     body=EDo(body=[ELiteral(raw="5", value=5.0)]),
        #                 )
        #             ],
        #         )
        #     ],
        # ),
    ],
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
    snapshot.assert_match(compile(EProgram([*BUILTINS, program])), id)
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
