from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, overload
from constraint import Constraint
import typed

import functools


class Substitution:
    def __init__(self, solutions: dict[typed.Var, typed.Type]) -> None:
        self.solutions = solutions

    @staticmethod
    def empty():
        return Substitution({})
    
    @staticmethod
    def from_pair(tvar: typed.Var, ty:typed.Type) -> Substitution:
        return Substitution({tvar: ty})


    def apply_constraints(self, constraints: set[Constraint]) -> set[Constraint]:
        return {*map(self.apply_constraint, constraints)}

    def apply_type(self, type: typed.Type) -> typed.Type:
        return functools.reduce(
            lambda result, solution: substitute(result, *solution),
            self.solutions.items(),
            type,
        )

    def apply_constraint(self, constraint: Constraint) -> Constraint:
        a, b = constraint
        return self.apply_type(a), self.apply_type(b)

    def compose(self,other:Substitution)->Substitution:
        substituted_this = map(other.apply_type,self.solutions.values())
        substituted_this = zip(self.solutions.keys(),substituted_this,)
        substituted_this = dict(substituted_this)
        
        return Substitution(substituted_this | other.solutions)


def substitute(ty:typed.Type, tvar:typed. Var,replacement:typed.Type)->typed.Type:
    substituteNext =functools.partial(substitute,tvar=tvar,replacement=replacement)

    match ty:
        case typed.number()|typed.string():
            return ty
        case typed.GenericType(value,params):
            return typed.GenericType(
                    substituteNext(value),
                    [*map(substituteNext,params)]
                )
        case typed.Var(tvar1) if (tvar == tvar1):
            return replacement
        case typed.Var(tvar1):
                return ty
        case _:
            raise TypeError(f"Cannot substitute {tvar} with {replacement} in {ty}")
