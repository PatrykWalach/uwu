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
        result = re.sub("([A-Z])", r"_\1", self.__class__.__name__).lower()
        result2 = f"fold{result}"
        if not hasattr(v, result2):
            raise ValueError(f"{v.__class__.__name__} does not have a {result2} method")
        return getattr(v, result2)(self)


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


class Fold:
    def default_fold(self, n: K) -> K:
        return n

    def fold_e_expr(self, n: terms.EExpr) -> terms.EExpr:
        return self.default_fold(n)

    def fold_e_block(self, n: terms.EBlock) -> terms.EBlock:
        return self.default_fold(n)

    def fold_e_program(self, n: terms.EProgram) -> terms.EProgram:
        return self.default_fold(n)

    def fold_e_binary_expr(self, n: terms.EBinaryExpr) -> terms.EBinaryExpr:
        return self.default_fold(n)

    def fold_e_do(self, n: terms.EDo) -> terms.EDo:
        return self.default_fold(n)

    def fold_e_literal(self, n: terms.ELiteral) -> terms.ELiteral:
        return self.default_fold(n)

    def fold_e_def(self, n: terms.EDef) -> terms.EDef:
        return self.default_fold(n)

    def fold_e_if(self, n: terms.EIf) -> terms.EIf:
        return self.default_fold(n)

    def fold_e_call(self, n: terms.ECall) -> terms.ECall:
        return self.default_fold(n)

    def fold_e_variant(self, n: terms.EVariant) -> terms.EVariant:
        return self.default_fold(n)

    def fold_e_variant_call(self, n: terms.EVariantCall) -> terms.EVariantCall:
        return self.default_fold(n)

    def fold_e_case_of(self, n: terms.ECaseOf) -> terms.ECaseOf:
        return self.default_fold(n)

    def fold_e_let(self, n: terms.ELet) -> terms.ELet:
        return self.default_fold(n)

    def fold_e_identifier(self, n: terms.EIdentifier) -> terms.EIdentifier:
        return self.default_fold(n)

    def fold_e_array(self, n: terms.EArray) -> terms.EArray:
        return self.default_fold(n)

    def fold_e_variantcall(self, n: terms.EVariantCall) -> terms.EVariantCall:
        return self.default_fold(n)

    def fold_e_external(self, n: terms.EExternal) -> terms.EExternal:
        return self.default_fold(n)

    def fold_e_unary_expr(self, n: terms.EUnaryExpr) -> terms.EUnaryExpr:
        return self.default_fold(n)

    def fold_e_pattern(self, n: terms.EPattern) -> terms.EPattern:
        return self.default_fold(n)

    def fold_e_enum_declaration(
        self, n: terms.EEnumDeclaration
    ) -> terms.EEnumDeclaration:
        return self.default_fold(n)

    def fold_e_hint(self, n: terms.EHint) -> terms.EHint:
        return self.default_fold(n)

    def fold_e_param(self, n: terms.EParam) -> terms.EParam:
        return self.default_fold(n)

    def fold_maybe_e_hint(self, n: terms.MaybeEHint) -> terms.MaybeEHint:
        return self.default_fold(n)

    def fold_e_case(self, n: terms.ECase) -> terms.ECase:
        return self.default_fold(n)

    def fold_e_match_variant(self, n: terms.EMatchVariant) -> terms.EMatchVariant:
        return self.default_fold(n)

    def fold_e_match_as(self, n: terms.EMatchAs) -> terms.EMatchAs:
        return self.default_fold(n)

    def fold_maybe_or_else(self, n: terms.MaybeOrElse) -> terms.MaybeOrElse:
        return self.default_fold(n)


class FoldAll(Fold):
    def default_fold(self, n: K) -> K:
        return n.fold_children_with(self)
