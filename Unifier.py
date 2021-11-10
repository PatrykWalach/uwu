from Substitution import Substitution
from constraint import Constraint


def unify(constraints: set[Constraint]) -> Substitution:
    if len(constraints) == 0:
        return Substitution.empty()
    
    subst:Substitution = unify_one(constraints.pop())
    substituted_tail = subst.apply_constraints(constraints)
    subst_tail: Substitution = unify(substituted_tail)
    return subst.compose(subst_tail)

import typed

def unify_one(constraint:Constraint)->Substitution:
    match constraint:
        case (typed.number, typed.number):
            return Substitution.empty()
        case (typed.GenericType(value0, [*params0]), typed.GenericType(value1, [*params1])) if  value0 == value1 and len(params0) == len(params1):
            return unify(
                set(zip(params0, params1))
            )
        case (typed.Var(tvar), ty)|(ty,typed.Var(tvar)):
            return unify_var(tvar,ty)
        case _:
            raise TypeError("Cannot unify types")

def unify_var(tvar:int, ty:typed.Type)->Substitution:
    match ty:
        case typed.Var(tvar2) if tvar == tvar2:
            return Substitution.empty()
        case typed.Var(_):
            return Substitution.from_pair(tvar,ty)
        case ty if occurs(tvar,ty):
            raise TypeError(f"circular use: {tvar} occurs in {ty}"
            )
        case ty:
            return Substitution.from_pair(tvar,ty)

import functools

def occurs(tvar:int, ty:typed.Type)->bool:
    next_occurs=functools.partial(occurs,tvar=tvar)

    match ty:
        case typed.GenericType(_, params):
            return any(next_occurs(ty=ty) for ty in params)
        case typed.Var(tvar2):
            return tvar == tvar2
        case _:
            return False