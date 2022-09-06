from __future__ import annotations

import dataclasses
import typing
from typing import TypeAlias


@dataclasses.dataclass(frozen=True)
class TCon:
    id: str
    kind: Kind
    alts: list[str] = dataclasses.field(default_factory=list)

    def w(self) -> Type:
        return self

    def __repr__(self) -> str:
        return f"{self.id}"


@dataclasses.dataclass(frozen=True)
class TVar:
    id: int
    kind: Kind

    def __repr__(self) -> str:
        return f"@{self.id}"


@dataclasses.dataclass
class TAp:
    con: Type
    arg: Type

    def __repr__(self) -> str:
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

    def w(self) -> Kind:
        return self


@dataclasses.dataclass
class KFun:
    arg: Kind
    ret: Kind


Kind: TypeAlias = KStar | KFun

TUnit = TCon("Unit", KStar())


TStr = TCon("Str", KStar())
TRegex = TCon("TRegex", KStar())


TNum = TCon("Num", KStar())
TFloat = TCon("Float", KStar())

TTupleCon = TCon("Tuple", KFun(KStar(), KFun(KStar(), KStar())))


def pair(a: Type, b: Type) -> TAp:
    return TAp(TAp(TTupleCon, a), b)


TCallable = TCon("Callable", KFun(KStar(), KFun(KStar(), KStar())))


def TDef(arg: Type, ret: Type) -> TAp:
    return TAp(TAp(TCallable, arg), ret)


TArrayCon = TCon("Array", KFun(KStar(), KStar()))


def TArray(t: Type) -> TAp:
    return TAp(TArrayCon, t)


SomeCon = TCon("Some", KFun(KStar(), KStar()))
NoneCon = TCon("None", KStar())
TOptionCon = TCon("Option", KFun(KStar(), KStar()), [SomeCon.id, NoneCon.id])


def TOption(t: Type) -> TAp:
    return TAp(TOptionCon, t)


TrueCon = TCon("True", KStar())
FalseCon = TCon("False", KStar())
TBool = TCon("Bool", KStar(), [TrueCon.id, FalseCon.id])


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
