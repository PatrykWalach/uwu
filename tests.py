from pathlib import WindowsPath
from subprocess import check_output
from compile import compile
from sly import lex
import json

from typing import Generic
import pytest
from algorithm_j import Scheme, UnifyException, type_infer
from main import BUILTINS, DEFAULT_CTX, AstEncoder, UwuLexer, UwuParser

import typed

from terms import *


@pytest.fixture
def parser():
    return UwuParser()


@pytest.fixture
def lexer():
    return UwuLexer()


def token(type, value, lineno, index):
    t = lex.Token()
    t.type = type
    t.value = value
    t.lineno = lineno
    t.index = index

    return t


# @pytest.mark.parametrize(
#     'program, expected_tokens', [
#         ("x:Option<Num>=None", [
#          token('IDENTIFIER', value='x', lineno=1, index=0),
#          token(type=':', value=':', lineno=1, index=1),
#          token(type='IDENTIFIER', value='Option', lineno=1, index=2),
#             token(type='<', value='<', lineno=1, index=8),
#             token(type='IDENTIFIER', value='Num', lineno=1, index=9),
#             token(type='>', value='>', lineno=1, index=15),
#             token(type='=', value='=', lineno=1, index=16),
#             token(type='IDENTIFIER', value='None', lineno=1, index=17),

#          ])
#     ])
# def test_tokenizer(program, expected_tokens, lexer):
#     tokens = [*lexer.tokenize(program)]
#     assert tokens == expected_tokens


@pytest.mark.parametrize(
    "program, ast",
    [
        ("1", [ELiteral("1", 1)]),
        ("'abc'", [ELiteral("'abc'", "abc")]),
        (
            "1+2*3",
            [
                EBinaryExpr(
                    "+",
                    ELiteral("1", 1),
                    EBinaryExpr("*", ELiteral("2", 2), ELiteral("3", 3)),
                )
            ],

        ),
        (
            "x=(2+3)*4",
            [
                EVariableDeclaration(
                    EIdentifier("x"),
                    EBinaryExpr(
                        "*",
                        EBinaryExpr("+", ELiteral("2", 2), ELiteral("3", 3)),
                        ELiteral("4", 4),
                    ),
                )
            ],

        ),
        # ("enum Option<value>{None\nSome(value)}\nx:Option<Num>=None"),
        (
            "def x(k) do k() end\ndef n() do 12 end\ny:Num=x(n)\nx",
            [
                EDef(
                    EIdentifier("x"),
                    [EParam(EIdentifier("k"))],
                    EDo([ECall(EIdentifier("k"), [])]),
                ),
                EDef(
                    EIdentifier("n"),
                    [],
                    EDo([ELiteral("12", 12)]),
                ),
                EVariableDeclaration(
                    EIdentifier("y"),
                    ECall(EIdentifier("x"), [EIdentifier("n")]),
                    hint=EHint(EIdentifier('Num'), []),
                ),
                EIdentifier("x"),
            ]
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
                EVariableDeclaration(
                    EIdentifier("x"),
                    EVariableDeclaration(
                        EIdentifier("y"),
                        EBinaryExpr("+", ELiteral("2", 2), ELiteral("3", 3)),
                    ),
                )
            ],

        ),
        (
            "do x = 1 end",
            [
                EDo(
                    [
                        EVariableDeclaration(
                            EIdentifier("x"),
                            ELiteral("1", 1),
                        )
                    ],
                )
            ],

        ),
        ("id('abc')", [
            ECall(EIdentifier("id"), [ELiteral("'abc'", "abc")])
        ], ),
        ("id(1)", [
            ECall(EIdentifier("id"), [ELiteral("1", 1)])
        ], ),
        ("id('12')\nid(1)", [ECall(EIdentifier("id"), [ELiteral("'12'", "12")]),
                             ECall(EIdentifier("id"), [ELiteral("1", 1)])
                             ], ),
        ("id(1+2)", [
            ECall(EIdentifier("id"), [
                EBinaryExpr("+", ELiteral("1", 1), ELiteral("2", 2))
            ])
        ], ),
        ("x:Option<Num>=None()", [
            EVariableDeclaration(EIdentifier(
                'x'), ECall(EIdentifier('None'), []),
                hint=EHint(EIdentifier('Option'), [
                           EHint(EIdentifier('Num'), [])])
            )]),
        (
            "def add(a, b) do a + b end",
            [
                EDef(
                    identifier=EIdentifier(name="add"),
                    params=[EParam(EIdentifier("a")),
                            EParam(EIdentifier("b"))],
                    body=EDo(
                        body=[
                            EBinaryExpr(
                                op="+",
                                left=EIdentifier(name="a"),
                                right=EIdentifier(name="b"),
                            )
                        ],
                        hint=None,
                    ),
                    hint=None,
                ),
            ],
        ),
        ('enum AOrB {A B}', [EEnumDeclaration(id=EIdentifier(name='AOrB'), generics=[], variants=[EVariant(id=EIdentifier(
            name='A'), fields=EFieldsUnnamed(unnamed=[])), EVariant(id=EIdentifier(name='B'), fields=EFieldsUnnamed(unnamed=[]))])]),
        ('case x of Some(value) do 2 end None() do 3 end end', [ECaseOf(EIdentifier(name='x'), [ECase(EEnumPattern(EIdentifier(name='Some'), [
            EParamPattern(EIdentifier(name='value'))]), EDo([ELiteral(raw='2', value=2.0)])), ECase(EEnumPattern(EIdentifier(name='None'), []), EDo([ELiteral(raw='3', value=3.0)]))])]),
    ],
)
def test_parser(program, ast, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    assert program == EProgram(ast)


@ pytest.mark.parametrize(
    "program, expected_type",
    [
        ("1", typed.TNum()),
        ("x = 1\nx", typed.TNum()),
        ("x = 1\na = x\na", typed.TNum()),
        ("x = 1\na = x", typed.TNum()),
        ("Some(1)", typed.TOption(typed.TNum())),
        ('id(id(1))', typed.TNum()),
        ("Some(Some(1))", typed.TOption(
         typed.TOption(typed.TNum()))),
        (
            "1+2*3",
            typed.TNum(),
        ),
        (
            "x=(2+3)*4",
            typed.TNum(),
        ),
        # ("enum Option<value>{None\nSome(value)}\nx:Option<Num>=None"),
        (
            "def id2(a) do a end\nid2('12')",
            typed.TStr()
        ),
        (
            "def fun() do fun() + 1 end\nfun()",
            typed.TNum()
        ),
        ('def fun() do: Num 1 end\n fun()', typed.TNum()),
        (
            "def id2(a) do a end\nid2(1)\nid2('12')",
            typed.TStr()
        ),
        (
            "def id2(a) do a end\nid2('12')\nid2(1)",
            typed.TNum()
        ),
        #     "def flatMap(v, fn) do case v of None do None end Some(value) do fn(value) end end end",
        (
            "x=y=2+3",
            typed.TNum(),
        ),
        (
            "do x = 1 end",
            typed.TNum(),
        ),
        ("id('12')", typed.TStr()),
        ("id(1)",  typed.TNum()),
        ("id('12')\nid(1)",  typed.TNum()),
        ("x:Option<Num>=None()", typed.TOption(typed.TNum())),
        ("id(1+2)",  typed.TNum()),
        (
            "def add(a, b) do a + b end",
            typed.TDef([typed.TNum(), typed.TNum()],    typed.TNum(),),
        ),
        ("if 2 > 0 then: Option<Num> None() else None() end",
         typed.TOption(typed.TNum())),
        ("if 2 > 0 then 1 else 2 end", typed.TNum()),
        ("if 2 > 0 then Some(Some(1)) end",
         typed.TOption(typed.TOption(typed.TNum()))),
        ("if 2 > 0 then Some(1) elif 2 > 0 then Some(1) end",
         typed.TOption(typed.TNum())),
        ("if 2 > 0 then Some(1) end",
         typed.TOption(typed.TNum())),
        ("if 2 > 0 then Some(1) elif 2 > 0 then None() end",
         typed.TOption(typed.TNum())),
        ('enum AB {A B}\nx:AB=A()', typed.TGeneric('AB', [])),
        ('enum ABC<x,y,z> {A(x)B(y)C(z)}\nx:ABC<Num,Num,Num>=A(1)',
         typed.TGeneric('ABC', [typed.TNum(), typed.TNum(), typed.TNum()])),
        ('x=Some(1)\ncase x of Some(value) do 2 end None() do 3 end end', typed.TNum()),
        ('def flatMap(v, fn) do case v of None() do None() end Some(value) do fn(value) end end end\nflatMap(Some(1),Some)',
         typed.TOption(typed.TNum())),
    ],
)
def test_infer(program, expected_type, parser, lexer):
    program = parser.parse(lexer.tokenize(program))

    assert type_infer(DEFAULT_CTX, program) == expected_type


@ pytest.mark.parametrize(
    "program, expected_output",
    [
        ("print(1)", "1"),
        ("x = 1\nprint(x)", "1"),
        ("x = 1\na = x\nprint(a)", "1"),
        ("x = 1\nprint(a = x)", "1"),
        ("print(1+2*3)", "7"),
        ("print(x=(2+3)*4)", "20"),
        ("print(if 2 > 0 then 1 else 2 end)", "1"),
        ("print(if 2 < 0 then 1 else 2 end)", "2"),
        ("print(case Some(1) of Some() do 2 end None() do 3 end end)", '2'),
        ("print(case Some(1) of Some(value) do 1 end None() do 3 end end)", '1'),
        ("enum ABC<a,b,c> {A(a) B(b) C(c)}\nprint(case A(1) of A(a) do a end B(b) do b end C(c) do c end end)", "1"),
        ("print(case Some(Some(1)) of Some(Some(value)) do value end None() do 2 end Some() do 3 end end)", "1"),
        ("print(case None() of Some(Some(value)) do value end None() do 2 end Some() do 3 end end)", "2"),
        ("print(case Some(None()) of Some(Some(value)) do value end None() do 2 end Some() do 3 end end)", "3"),
        ("enum Pair<a,b> {Pair(a,b)}\nprint(case Pair(1,2) of Pair(x, y) do x end end)", "1"),
        ("enum Pair<a,b> {Pair(a,b)}\nprint(case Pair(1,2) of Pair(x, y) do y end end)", "2"),
        ("enum Pair<a,b> {Pair(a,b)}\nprint(case Pair(1,2) of Pair(a) do a end end)", "1"),
        ("enum Pair<a,b> {Pair(a,b)}\nprint(case Pair(1,Pair(2,3)) of Pair(x, Pair(y, z)) do z end Pair(c, v) do c end end)", "3"),
    ],
)
def test_compile_with_snapshot(program, expected_output, snapshot, parser, lexer):
    program = parser.parse(lexer.tokenize(program))
    snapshot.assert_match(compile(EProgram(BUILTINS+program.body)), 'index.js')
    path: WindowsPath = snapshot.snapshot_dir
    assert check_output(['node', path / 'index.js']
                        ) == f"{expected_output}\n".encode('UTF-8')


@ pytest.mark.parametrize(
    "program",
    [
        "x: Str = 134",
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
