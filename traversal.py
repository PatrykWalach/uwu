import dataclasses
import functools
import typing

S = typing.TypeVar("S")
T = typing.TypeVar("T")
A = typing.TypeVar("A")
B = typing.TypeVar("B")


Traversal: typing.TypeAlias = typing.Callable[[typing.Callable[[S], T], A], B]

Traversal1: typing.TypeAlias = Traversal[S, S, A, A]
Fmap: typing.TypeAlias = typing.Callable[[A], A]


def over(t: Traversal1[A, B], f: Fmap[B], v: A) -> A:
    ...


def toListOf(t: Traversal1[A, B], v: B) -> list[A]:
    ...


def set(t: Traversal1[B, A], v0: B, v1: A) -> A:
    ...


def traverse(f: Fmap[list[A]], v: A) -> A:
    ...


import terms
import operator
import functools

import builtins


def id(v: A) -> A:
    return v


def dot(f0: Traversal1[B, S], g: Traversal1[A, B]) -> Traversal1[A, S]:
    def fg(f1: Fmap[A], v: S) -> S:
        return f0(lambda v2: g(f1, v2), v)

    return fg


def dot3(
    f0: Traversal1[B, S], g: Traversal1[A, B], h: Traversal1[T, A]
) -> Traversal1[T, S]:
    return dot(dot(f0, g), h)


K = typing.TypeVar("K")


def dot4(
    f0: Traversal1[B, S], g: Traversal1[A, B], h: Traversal1[T, A], i: Traversal1[K, T]
) -> Traversal1[K, S]:
    return dot(dot3(f0, g, h), i)


P0 = typing.ParamSpec("P0")
P1 = typing.ParamSpec("P1")

import itertools


def universeOf(t: Traversal1[A, A], v: A) -> list[A]:
    return list(
        itertools.chain(
            [v],
            itertools.chain.from_iterable((universeOf(t, vx) for vx in toListOf(t, v))),
        )
    )


def universeOn(t: Traversal1[A, S], v: S) -> list[A]:
    return list(
        itertools.chain.from_iterable(universeOn(children_of(type(vx)), vx) for vx in toListOf(t, v))
    )






def id_getter(program: terms.EProgram) -> typing.Set[str]:

    ids = toListOf(
        dot(
            children_of(list[terms.EExpr]),
            children_of(terms.EExpr),
            # children_of(terms.EIdentifier),
            # children_of(str),
        ),
        program,
    )

    ops = toListOf(
        dot4(
            children_of(list[terms.EExpr]),
            children_of(terms.EExpr),
            children_of(terms.EBinaryExpr),
            children_of(str),
        ),
        program,
    )

    return builtins.set(ids + ops)


def children_of(*cons: typing.Type[A]) -> Traversal1[A, typing.Any]:
    def t(f: Fmap[A], v: typing.Any) -> typing.Any:
        if isinstance(list, v):
            return list((f(vx) if isinstance(vx, cons) else vx for vx in v))

        if isinstance(tuple, v):
            return tuple((f(vx) if isinstance(vx, cons) else vx for vx in v))

        if dataclasses.is_dataclass(v):
            fields = {
                field.name: getattr(v, field.name) for field in dataclasses.fields(v)
            }

            return dataclasses.replace(
                v,
                **{
                    key: f(value)
                    for key, value in fields.items()
                    if isinstance(value, cons)
                },
            )

        return v

    return t

    # def program_exprs(f: Fmap[terms.EExpr], v: terms.EProgram) -> terms.EProgram:
    #     return terms.EProgram(list(map(f, v.body)))

    # def expr_id(f: Fmap[terms.EIdentifier], v: terms.EExpr) -> terms.EExpr:
    #     match v.expr:
    #         case terms.EIdentifier() as id:
    #             return terms.EExpr(f(id))
    #     return v

    # def id_name(f: Fmap[str], v: terms.EIdentifier) -> terms.EIdentifier:
    #     return terms.EIdentifier(f(v.name))


if __name__ =='__main__':
    @dataclasses.dataclass
    class EAdd:
        left: "EExp"
        right: "EExp"

    @dataclasses.dataclass
    class ELit:
        value:int

    EExp = EAdd| ELit
    print(universeOf(children_of(EAdd, ELit), EAdd(ELit(1), EAdd(ELit(2), ELit(0)))))
    print(universeOn(children_of(EAdd, ELit), EAdd(ELit(1), EAdd(ELit(2), ELit(0)))))
