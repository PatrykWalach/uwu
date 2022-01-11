import json
from dataclasses import dataclass
from pathlib import WindowsPath
from subprocess import check_output
from typing import Generic

import pytest
from sly import lex

import typed
from algorithm_j import Scheme, UnifyException, type_infer
from compile import compile
from main import BUILTINS, DEFAULT_CTX, AstEncoder, UwuLexer, UwuParser
from terms import *


@pytest.fixture
def parser():
    return UwuParser()


@pytest.fixture
def lexer():
    return UwuLexer()


# @dataclass
# class Token:
#     type: str
#     value: str

#     @classmethod
#     def from_token(cls, t: lex.Token):
#         return cls(t.type, t.value)


# @pytest.mark.parametrize(
#     'program, expected_tokens', [

# ("x:Option<Num>=None", [
#  token('IDENTIFIER', value='x', lineno=1, indelet x=0),
#  token(type=':', value=':', lineno=1, indelet x=1),
#  token(type='IDENTIFIER', value='Option', lineno=1, indelet x=2),
#     token(type='<', value='<', lineno=1, indelet x=8),
#     token(type='IDENTIFIER', value='Num', lineno=1, indelet x=9),
#     token(type='>', value='>', lineno=1, indelet x=15),
#     token(type='=', value='=', lineno=1, indelet x=16),
#     token(type='IDENTIFIER', value='None', lineno=1, indelet x=17),

#  ])

#         ('case [Some(1), None()] of [Some(value), None()] do value end [None(), Some(value)] do 3 end [] do 4 end [...arr] do 5 end end', [
#             Token(type='CASE', value='case'),
#             Token(type='[', value='['),
#             Token(type='TYPE_IDENTIFIER', value='Some'),
#             Token(type='(', value='('),
#             Token(type='NUMBER', value='1'),
#             Token(type=')', value=')'),
#             Token(type=',', value=','),
#             Token(type='TYPE_IDENTIFIER', value='None'),
#             Token(type='(', value='('),
#             Token(type=')', value=')'),
#             Token(type=']', value=']'),
#             Token(type='OF', value='of'),
#             Token(type='[', value='['),
#             Token(type='TYPE_IDENTIFIER', value='Some'),
#             Token(type='(', value='('),
#             Token(type='IDENTIFIER', value='value'),
#             Token(type=')', value=')'),
#             Token(type=',', value=','),
#             Token(type='TYPE_IDENTIFIER', value='None'),
#             Token(type='(', value='('),
#             Token(type=')', value=')'),
#             Token(type=']', value=']'),
#             Token(type='DO', value='do'),
#             Token(type='IDENTIFIER', value='value'),
#             Token(type='END', value='end'),
#             Token(type='[', value='['),
#             Token(type='TYPE_IDENTIFIER', value='None'),
#             Token(type='(', value='('),
#             Token(type=')', value=')'),
#             Token(type=',', value=','),
#             Token(type='TYPE_IDENTIFIER', value='Some'),
#             Token(type='(', value='('),
#             Token(type='IDENTIFIER', value='value'),
#             Token(type=')', value=')'),
#             Token(type=']', value=']'),
#             Token(type='DO', value='do'),
#             Token(type='NUMBER', value='3'),
#             Token(type='END', value='end'),
#             Token(type='[', value='['),
#             Token(type=']', value=']'),
#             Token(type='DO', value='do'),
#             Token(type='NUMBER', value='4'),
#             Token(type='END', value='end'),
#             Token(type='[', value='['),
#             Token(type='SPREAD', value='...'),
#             Token(type='IDENTIFIER', value='arr'),
#             Token(type=']', value=']'),
#             Token(type='DO', value='do'),
#             Token(type='NUMBER', value='5'),
#             Token(type='END', value='end'),
#             Token(type='END', value='end'),
#         ])
#     ])
# def test_tokenizer(program, expected_tokens, lexer):
#     tokens = map(Token.from_token, lexer.tokenize(program))
#     assert [*tokens] == expected_tokens


@pytest.mark.parametrize(
    "program, ast",
    [
        ("1", [ELiteral(1)]),
        ("'abc'", [ELiteral("abc")]),
        ("-2+2", [EBinaryExpr("+", EUnaryExpr("-", ELiteral(2)), ELiteral(2))]),
        ("-(2+2)", [EUnaryExpr("-", EBinaryExpr("+", ELiteral(2), ELiteral(2)))]),
        ("let x=2\n-1", [ELet("x", ELiteral(2)), EUnaryExpr("-", ELiteral(1))]),
        ("let x=2-1", [ELet("x", EBinaryExpr("-", ELiteral(2), ELiteral(1)))]),
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
            "let x=id(2)",
            [ELet("x", ECall(EIdentifier("id"), [ELiteral(2)]))],
        ),
        (
            "(let x=id)(2)",
            [ECall(ELet("x", EIdentifier("id")), [ELiteral(2)])],
        ),
        (
            "let x=id\n(2)",
            [ELet("x", EIdentifier("id")), ELiteral(2)],
        ),
        (
            "let x=2\n-id(2)",
            [
                ELet(
                    "x",
                    EBinaryExpr(
                        "-", ELiteral(2), ECall(EIdentifier("id"), [ELiteral(2)])
                    ),
                )
            ],
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
            "let x=(2+3)*4",
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
            "enum StrOrNum{String(Str)\nNumber(Num)}\nlet x=Number(1)\nlet x=String('12')",
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
            "def x(k) do k() end\ndef n() do 12 end\nlet y:Num=x(n)\nx",
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
            "let x=let y=2+3",
            [ELet("x", ELet("y", EBinaryExpr("+", ELiteral(2), ELiteral(3))))],
        ),
        (
            "do let x = 1 end",
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
            "let x:Option<Num>=None()",
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
                            {
                                "$": EMatchVariant(
                                    id="Some",
                                    patterns=[EMatchAs("value")],
                                )
                            },
                            EDo([ELiteral(value=2.0)]),
                        ),
                        ECase(
                            {"$": EMatchVariant("None")},
                            EDo([ELiteral(value=3.0)]),
                        ),
                    ],
                )
            ],
        ),
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
        ("let x=1\nx", typed.TNum()),
        ("let x=1\nlet a=x\na", typed.TNum()),
        ("let x=1\nlet a=x", typed.TNum()),
        ("Some(1)", typed.TOption(typed.TNum())),
        ("id(id(1))", typed.TNum()),
        ("2+id(1)", typed.TNum()),
        ("Some(Some(1))", typed.TOption(typed.TOption(typed.TNum()))),
        (
            "1+2*3",
            typed.TNum(),
        ),
        (
            "let x=(2+3)*4",
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
        ("let x=Some(1)\nlet x:Option<Str>=None()", typed.TOption(typed.TStr())),
        (
            "let x=y=2+3",
            typed.TNum(),
        ),
        (
            "do let x=1 end",
            typed.TNum(),
        ),
        ("id('12')", typed.TStr()),
        ("id(1)", typed.TNum()),
        ("id('12')\nid(1)", typed.TNum()),
        ("let x:Option<Num>=None()", typed.TOption(typed.TNum())),
        ("id(1+2)", typed.TNum()),
        (
            "def add(a, b) do a + b end",
            typed.TDef(typed.TNum(), typed.TDef(typed.TNum(), typed.TNum())),
        ),
        ("if 2 > 0 then 1 else 2 end", typed.TNum()),
        (
            "if 2 > 0 then Some(Some(1)) else None end",
            typed.TOption(typed.TOption(typed.TNum())),
        ),
        (
            "if 2 > 0 then Some(1) elif 2 > 0 then Some(1) else None end",
            typed.TOption(typed.TNum()),
        ),
        ("if 2 > 0 then Some(1) else None end", typed.TOption(typed.TNum())),
        (
            "if 2 > 0 then Some(1) elif 2 > 0 then None() else None end",
            typed.TOption(typed.TNum()),
        ),
        ("enum AB{A B}\nlet x:AB=A()", typed.TCon("AB", typed.KStar())),
        (
            "enum ABC<X,Y,Z> {A(X)B(Y)C(Z)}\nlet x:ABC<Num,Num,Num>=A(1)",
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
                        ),
                        typed.TNum(),
                    ),
                    typed.TNum(),
                ),
                typed.TNum(),
            ),
        ),
        (
            "let x=Some(1)\ncase x of Some(value) do 2 end None() do 3 end end",
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
            "enum StrOrNum{String(Str)\nNumber(Num)}\nlet x=Number(1)\nlet x=String('12')",
            typed.TCon("StrOrNum", typed.KStar()),
        ),
        # ("{1,'2'}", typed.TTuple([typed.TNum(), typed.TStr()])),
    ],
)
def test_infer(program, expected_type, parser, lexer):
    program = parser.parse(lexer.tokenize(program))

    assert type_infer(DEFAULT_CTX, program) == expected_type


@pytest.mark.parametrize(
    "id, program, expected_output",
    (
        (
            [
                ("0", "`console.log`(1)", "1"),
                ("1", "let x=1\n`console.log`(x)", "1"),
                ("2", "let x=1\nlet a = x\n`console.log`(a)", "1"),
                ("3", "let x=1\n`console.log`(let a = x)", "1"),
                ("4", "`console.log`(1+2*3)", "7"),
                ("5", "`console.log`(let x=(2+3)*4)", "20"),
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
                    "def add(a, b) do a + b end\nlet addTwo=add(2)\n`console.log`(addTwo(3))",
                    "5",
                ),
                (
                    "23",
                    "def add(a) do def add(b) do a + b end end\nlet addTwo=add(2)\n`console.log`(addTwo(3))",
                    "5",
                ),
                ("24", "def add(a, b) do a + b end\n\n`console.log`(add(2,3))", "5"),
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
    "program",
    [
        "let x: Str = 134",
        "do: Str 1 end",
        "def fun(): Str do 1 end",
        "if 2 > 0 then: Num 1 else '12' end",
        "if 2 > 0 then: Num '12' else 1 end",
        "if 2 > 0 then: Num 1 elif 2 > 0 then '12' else 1 end",
        "if 1+1 then 1 else 1 end",
        "if 2 > 0 then: Str 1 else 2 end",
    ],
)
def test_do_expection(program, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    with pytest.raises(UnifyException):
        type_infer(DEFAULT_CTX, program)
