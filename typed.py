from __future__ import annotations
import dataclasses
from typing import TypeAlias

@dataclasses.dataclass(frozen=True)
class number:
    pass

@dataclasses.dataclass(frozen=True)
class string:
    pass

@dataclasses.dataclass(frozen=True)
class GenericType:
    id: str
    params: tuple[Type,...]

@dataclasses.dataclass(frozen=True)
class Var:
    type: int

Type:TypeAlias = number|string|Var |GenericType

