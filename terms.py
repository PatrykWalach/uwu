from __future__ import annotations

import dataclasses
import re
import typing

import terms

T = typing.TypeVar("T")


TFoldWith = typing.TypeVar("TFoldWith", bound="FoldWith")


class FoldWith(typing.Protocol):
    def fold_children_with(self: TFoldWith, v: FoldAll) -> TFoldWith:
        self_items = (
            (field.name, getattr(self, field.name))
            for field in dataclasses.fields(self)
        )

        return dataclasses.replace(
            self,
            **{
                key: [value2.fold_with(v) for value2 in value]
                if isinstance(value, list)
                else value.fold_with(v)
                for key, value in self_items
                if dataclasses.is_dataclass(value) or isinstance(value, list)
            },
        )

    def fold_with(self: TFoldWith, v: FoldAll) -> TFoldWith:
        # result = re.sub("([A-Z])", r"_\1", self.__class__.__name__).lower()
        # result2 = f"fold{result}"
        result2 = self.__class__.__name__
        if not hasattr(v, result2):
            raise ValueError(f"{v.__class__.__name__} does not have a {result2} method")
        return typing.cast(TFoldWith, getattr(v, result2)(self))


TPipable = typing.TypeVar("TPipable", bound="Pipable")

R = typing.TypeVar("R")


class Pipable:
    def __rshift__(self: TPipable, other: typing.Callable[[TPipable], R]) -> R:
        return other(self)

    def __rlshift__(self: TPipable, other: typing.Callable[[TPipable], R]) -> R:
        return other(self)


class Node(Pipable, FoldWith):
    pass


@dataclasses.dataclass(frozen=True)
class EBlock(Node):
    body: list[EExpr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EHint(Node):
    id: str
    args: list[EHint] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class Maybe(Node, typing.Generic[T]):
    value: typing.Optional[T] = None


@dataclasses.dataclass(frozen=True)
class MaybeEHint(Maybe[EHint]):
    pass


@dataclasses.dataclass(frozen=True)
class ELet(Node):
    id: str
    init: EExpr
    hint: MaybeEHint = MaybeEHint()


@dataclasses.dataclass(frozen=True)
class EDo(Node):
    block: EBlock = EBlock()
    hint: MaybeEHint = MaybeEHint()


@dataclasses.dataclass(frozen=True)
class EProgram(Node):
    body: list[EExpr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EBinaryExpr(Node):
    op: typing.Literal["++", "+", "-", "/", "*", "%", "//", ">", "<", "|", "!=", "=="]
    left: EExpr
    right: EExpr


@dataclasses.dataclass(frozen=True)
class EIdentifier(Node):
    name: str


@dataclasses.dataclass(frozen=True)
class ELiteral(Node):
    value: float | str


@dataclasses.dataclass(frozen=True)
class EExternal(Node):
    value: str


@dataclasses.dataclass(frozen=True)
class EDef(Node):
    identifier: str
    params: list[EParam]
    body: EDo
    hint: MaybeEHint = MaybeEHint()
    generics: list[EIdentifier] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EParam(Node):
    identifier: str
    hint: MaybeEHint = MaybeEHint()


@dataclasses.dataclass(frozen=True)
class EUnaryExpr(Node):
    op: typing.Literal["-"]
    expr: EExpr


@dataclasses.dataclass(frozen=True)
class EMatchAs(Node):
    identifier: str


@dataclasses.dataclass(frozen=True)
class ECaseOf(Node):
    expr: EExpr
    cases: list[ECase] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class ECase(Node):
    pattern: EPattern
    body: EDo = dataclasses.field(default_factory=EDo)


@dataclasses.dataclass(frozen=True)
class EMatchVariant(Node):
    id: str
    patterns: list[EPattern] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class ECall(Node):
    callee: EExpr
    args: list[EExpr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EVariantCall(Node):
    callee: str
    args: list[EExpr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EArray(Node):
    args: list[EExpr] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class MaybeOrElse(Maybe["OrElse"]):
    pass


@dataclasses.dataclass(frozen=True)
class EIf(Node):
    test: EExpr
    then: EBlock
    or_else: MaybeOrElse = MaybeOrElse()
    hint: MaybeEHint = MaybeEHint()


OrElse: typing.TypeAlias = EBlock | EIf


@dataclasses.dataclass(frozen=True)
class EEnumDeclaration(Node):
    id: str
    variants: list[EVariant] = dataclasses.field(default_factory=list)
    generics: list[EIdentifier] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EVariant(Node):
    id: str
    fields: list[EHint] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EMatchArray:
    patterns: list[EPattern]
    rest: EIdentifier | None = None


@dataclasses.dataclass(frozen=True)
class EMatchTuple:
    patterns: list[EPattern]
    rest: EIdentifier | None = None


@dataclasses.dataclass(frozen=True)
class EFieldsUnnamed:
    unnamed: list[EIdentifier]


@dataclasses.dataclass(frozen=True)
class EPattern(Node):
    pattern: EMatchAs | EMatchVariant


P = typing.ParamSpec("P")
S = typing.TypeVar("S")
D = typing.TypeVar("D")


def compose(
    f: typing.Callable[[D], S], g: typing.Callable[P, D], /
) -> typing.Callable[P, S]:
    def h(*args: P.args, **kwargs: P.kwargs) -> S:
        return f(g(*args, **kwargs))

    return h


@dataclasses.dataclass(frozen=True)
class EExpr(Node):
    expr: (
        EDo
        | ELiteral
        | EDef
        | EIf
        | ECall
        | ECaseOf
        | ELet
        | EIdentifier
        | EBinaryExpr
        | EArray
        | EVariantCall
        | EExternal
        | EUnaryExpr
        | EEnumDeclaration
    )


K = typing.TypeVar("K", bound=terms.FoldWith)


class FoldMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        nodes = namespace.get("_nodes_", [])
        for node in nodes:
            exec(f"def {node}(self, n): return self.fold(n)", globals(), namespace)

        return super().__new__(cls, name, bases, namespace, **kwargs)


class NodeFold(metaclass=FoldMeta):

    _nodes_ = [
        "EExpr",
        "EBlock",
        "EProgram",
        "EBinaryExpr",
        "EDo",
        "ELiteral",
        "EDef",
        "EIf",
        "ECall",
        "EVariant",
        "EVariantCall",
        "ECaseOf",
        "ELet",
        "EIdentifier",
        "EArray",
        "EVariantCall",
        "EExternal",
        "EUnaryExpr",
        "EPattern",
        "EEnumDeclaration",
        "EHint",
        "EParam",
        "MaybeEHint",
        "ECase",
        "EMatchVariant",
        "EMatchAs",
        "MaybeOrElse",
    ]


class Fold(NodeFold):
    def fold(self, n: K) -> K:
        return n


class FoldAll(NodeFold):
    def fold(self, n: K) -> K:
        return n.fold_children_with(self)
