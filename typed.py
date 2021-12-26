from __future__ import annotations
import dataclasses
from typing import TypeAlias


@dataclasses.dataclass(frozen=True)
class TGeneric:
    id: str
    params: list[Type]

    def __str__(self) -> str:
        params = (
            "" if len(self.params) < 1 else "<" + ",".join(map(str, self.params)) + ">"
        )
        return f"{type(self).__name__}{params}"


@dataclasses.dataclass(frozen=True)
class TVar:
    type: int


def TDef(param: Type, ret: Type) -> Type:
    return TGeneric("Def", [param, ret])


def TThunk(ret: Type) -> Type:
    return TDef(TUnit(), ret)


def TNum() -> Type:
    return TGeneric("Num", [])


def TUnit() -> Type:
    return TGeneric("Unit", [])


def TStr() -> Type:
    return TGeneric("Str", [])


def TBool() -> Type:
    return TGeneric("Bool", [])


def TOption(param: Type) -> Type:
    return TGeneric("Option", [param])


def TArray(param: Type) -> Type:
    return TGeneric("Array", [param])

def TTuple(types: list[Type]) -> Type:
    return TGeneric("TTuple", types)


Type: TypeAlias = TVar | TGeneric
