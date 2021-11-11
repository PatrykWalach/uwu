from __future__ import annotations
import dataclasses
from typing import TypeAlias

@dataclasses.dataclass(frozen=True)
class TNum:
    pass

@dataclasses.dataclass(frozen=True)
class TStr:
    pass

@dataclasses.dataclass(frozen=True)
class TGeneric:
    id: str
    params: tuple[Type,...]

def TDef(params: tuple[Type,...], ret: Type) -> Type:
    return TGeneric('Def', (TGeneric('Params', params),ret))

@dataclasses.dataclass(frozen=True)
class TVar:
    type: int

Type:TypeAlias = TNum|TStr|TVar |TGeneric

