from __future__ import annotations

import dataclasses
import typing
from typing import TypeAlias


@dataclasses.dataclass(frozen=True)
class TCon:
    id: str
    kind: Kind
    alts: list[str] = dataclasses.field(default_factory=list)

    def __repr__(self):
        return f"{self.id}"


@dataclasses.dataclass(frozen=True)
class TVar:
    id: int
    kind: Kind

    def __repr__(self):
        return f"@{self.id}"


@dataclasses.dataclass
class TAp:
    con: Type
    arg: Type

    def __repr__(self):
        match self.con:
            case TCon("Array"):
                return f"[{self.arg}]"
            case TAp(TCon("Callable"), TAp() as arg):
                return f"({arg!r}) -> {self.arg}"
            case TAp(TCon("Callable"), arg):
                return f"{arg!r} -> {self.arg}"

        return f"{self.con!r}<{self.arg!r}>".replace("><", ", ")


Type: TypeAlias = TVar | TCon | TAp


@dataclasses.dataclass
class KStar:
    pass


@dataclasses.dataclass
class KFun:
    arg: Kind
    ret: Kind


Kind: TypeAlias = KStar | KFun


def TUnit():
    return TCon("Unit", KStar())


def TStr():
    return TCon("Str", KStar())


def TNum():
    return TCon("Num", KStar())


def TTupleCon():
    return TCon("Tuple", KFun(KStar(), KFun(KStar(), KStar())))


def pair(a: Type, b: Type):
    return TAp(TAp(TTupleCon(), a), b)


def TCallableCon():
    return TCon("Callable", KFun(KStar(), KFun(KStar(), KStar())))


def TDef(arg: Type, ret: Type):
    return TAp(TAp(TCallableCon(), arg), ret)


def TArrayCon():
    return TCon("Array", KFun(KStar(), KStar()))


def TArray(t: Type):
    return TAp(TArrayCon(), t)


def TOptionCon():
    return TCon("Option", KFun(KStar(), KStar()), ["Some", "None"])


def TOption(t: Type):
    return TAp(TOptionCon(), t)


def TBool():
    return TCon("Bool", KStar(), ["True", "False"])


def kind(t: Type) -> Kind:
    match t:
        case TVar(_, k):
            return k
        case TCon(_, k):
            return k
        case TAp(arg):
            match kind(arg):
                case KFun(_, k):
                    return k

    raise TypeError(f"kind of {t}")


def assert_never(value: typing.NoReturn) -> typing.NoReturn:
    # This also works at runtime as well
    assert False, f"This code should never be reached, got: {value}"
