from __future__ import annotations
import dataclasses
from typing import TypeAlias


@dataclasses.dataclass(frozen=True)
class TGeneric:
    id: str
    params: list[Type]

    def __str__(self) -> str:
        params = ''if len(self.params) < 1 else '<' + \
            ','.join(map(str, self.params))+'>'
        return f"{type(self).__name__}{params}"


def TDef(params: list[Type], ret: Type) -> Type:
    return TGeneric('Def', [TGeneric('Params', params), ret])


def TNum() -> Type:
    return TGeneric('Num', [])


def TStr() -> Type:
    return TGeneric('Str', [])


def TBool() -> Type:
    return TGeneric('Bool', [])


@dataclasses.dataclass(frozen=True)
class TVar:
    type: int


Type: TypeAlias = TVar | TGeneric
