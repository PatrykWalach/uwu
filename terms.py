from __future__ import annotations

import dataclasses
import typing



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

    def __rpow__(self: TPipable, other: typing.Callable[[TPipable], R]) -> R:
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
class EMaybeHintNothing(Node):
    pass


@dataclasses.dataclass(frozen=True)
class EMaybeHint(Node):
    value: EMaybeHintNothing | EHint = EMaybeHintNothing()


@dataclasses.dataclass(frozen=True)
class ELet(Node):
    id: str
    init: EExpr
    hint: EMaybeHint = EMaybeHint()


@dataclasses.dataclass(frozen=True)
class EDo(Node):
    block: EBlock = EBlock()
    hint: EMaybeHint = EMaybeHint()

import Ctx
@dataclasses.dataclass(frozen=True)
class EProgram(Node):
    body: list[EExpr] = dataclasses.field(default_factory=list)
    ctx: Ctx.Context = dataclasses.field(default_factory=dict)

    def __add__(self, program: EProgram) -> EProgram:
        assert isinstance(program, EProgram)
        return EProgram(self.body + program.body, self.ctx | program.ctx)


BinaryOp = typing.Literal[
    "<>",
    "+",
    "-",
    "/",
    "*",
    "<",
    ">",
    "!=",
    "==",
    "||",
    "or",
    "&&",
    "and",
    "=~",
    "<=",
    ">=",
    "++",
    "+.",
    "-.",
    "/.",
    "*.",
    "**",
    "**.",
]


@dataclasses.dataclass(frozen=True)
class EBinaryExpr(Node):

    op: BinaryOp
    left: EExpr
    right: EExpr


@dataclasses.dataclass(frozen=True)
class EIdentifier(Node):
    name: str


@dataclasses.dataclass(frozen=True)
class ENumLiteral(Node):
    value: float


@dataclasses.dataclass(frozen=True)
class EFloatLiteral(Node):
    value: float


@dataclasses.dataclass(frozen=True)
class EStrLiteral(Node):
    value: str


@dataclasses.dataclass(frozen=True)
class EInter(Node):
    left: str
    mid: "EExpr"
    right: EInterOrStr


@dataclasses.dataclass(frozen=True)
class EInterOrStr(Node):
    value: EInter | EStrLiteral


@dataclasses.dataclass(frozen=True)
class EExternal(Node):
    value: str


@dataclasses.dataclass(frozen=True)
class EDef(Node):
    identifier: str
    params: list[EParam]
    body: EDo
    hint: EMaybeHint = EMaybeHint()
    generics: list[EIdentifier] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EBinaryOpDef(Node):
    identifier: BinaryOp
    params: list[EParam]
    body: EDo
    hint: EMaybeHint = EMaybeHint()
    generics: list[EIdentifier] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EParam(Node):
    identifier: str
    hint: EMaybeHint = EMaybeHint()


@dataclasses.dataclass(frozen=True)
class EUnaryExpr(Node):
    op: typing.Literal["-", "+", "!", "not"]
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
class EIf(Node):
    test: EExpr
    then: EBlock
    or_else: EMaybeOrElse = dataclasses.field(default_factory=lambda: EMaybeOrElse())
    hint: EMaybeHint = EMaybeHint()


@dataclasses.dataclass(frozen=True)
class EMaybeOrElseNothing(Node):
    pass


@dataclasses.dataclass(frozen=True)
class EMaybeOrElse(Node):

    value: EBlock | EIf | EMaybeOrElseNothing = EMaybeOrElseNothing()


@dataclasses.dataclass(frozen=True)
class EEnumDeclaration(Node):
    id: str
    _: dataclasses.KW_ONLY
    variants: list[EVariant] = dataclasses.field(default_factory=list)
    generics: list[EIdentifier] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class EVariant(Node):
    id: str
    fields: list[EHint] = dataclasses.field(default_factory=list)


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
        | ENumLiteral
        | EBinaryOpDef
        | EFloatLiteral
        | EStrLiteral
        | EInter
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


K = typing.TypeVar("K", bound=FoldWith)


class FoldMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        # nodes = globals().keys()
        # import terms
        # nodes = terms.__dict__.keys()
        nodes = namespace.get("_nodes_", [])

        for node in nodes:
            if not node.startswith("E"):
                continue
            exec(f"def {node}(self, n): return self.fold(n)", globals(), namespace)

        return super().__new__(cls, name, bases, namespace, **kwargs)


class NodeFold(metaclass=FoldMeta):
    _nodes_ = {
        EExpr.__name__,
        EBlock.__name__,
        EProgram.__name__,
        EBinaryExpr.__name__,
        EDo.__name__,
        ENumLiteral.__name__,
        EFloatLiteral.__name__,
        EStrLiteral.__name__,
        EDef.__name__,
        EIf.__name__,
        ECall.__name__,
        EVariant.__name__,
        EVariantCall.__name__,
        ECaseOf.__name__,
        ELet.__name__,
        EIdentifier.__name__,
        EArray.__name__,
        EVariantCall.__name__,
        EExternal.__name__,
        EUnaryExpr.__name__,
        EPattern.__name__,
        EEnumDeclaration.__name__,
        EHint.__name__,
        EParam.__name__,
        EMaybeHint.__name__,
        ECase.__name__,
        EMatchVariant.__name__,
        EMatchAs.__name__,
        EMaybeOrElse.__name__,
        EInter.__name__,
        EMaybeHintNothing.__name__,
        EStrLiteral.__name__,
        ENumLiteral.__name__,
        EBinaryOpDef.__name__,
        EInterOrStr.__name__,
    }


class Fold(NodeFold):
    def fold(self, n: K) -> K:
        return n


class FoldAll(NodeFold):
    def fold(self, n: K) -> K:
        return n.fold_children_with(self)


AstNode: typing.TypeAlias = (
    EIdentifier
    | EExpr
    | EInter
    | EMaybeHint
    | EProgram
    | EBinaryOpDef
    | EParam
    | EInterOrStr
    | EUnaryExpr
    | EMaybeOrElse
    | EMaybeOrElse
    | EVariantCall
    | EArray
    | EBinaryExpr
    | EBlock
    | EHint
    | EMaybeHintNothing
    | ECall
    | ECaseOf
    | EDef
    | EDo
    | EEnumDeclaration
    | EExpr
    | EIf
    | EStrLiteral
    | EMaybeOrElseNothing
    | ENumLiteral
    | EFloatLiteral
    | ECall
    | ECaseOf
    | ELet
    | EIdentifier
    | EBinaryExpr
    | EArray
    | EVariantCall
    | EExternal
    | EUnaryExpr
)
