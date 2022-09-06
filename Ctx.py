from __future__ import annotations

import dataclasses
import typing

import typed


@dataclasses.dataclass
class Scheme:
    vars: list[int]
    ty: typed.Type

    @staticmethod
    def from_subst(subst: Substitution, ctx: Context, ty1: typed.Type)->Scheme:
        ftv = free_type_vars(apply_subst(subst, ty1))
        ftv -= free_type_vars_ctx(apply_subst_ctx(subst, ctx))

        return Scheme(list(ftv), apply_subst(subst, ty1))


Substitution: typing.TypeAlias = dict[int, typed.Type]
Context: typing.TypeAlias = dict[str, Scheme]


def apply_subst(subst: Substitution, ty: typed.Type) -> typed.Type:
    match ty:
        case typed.TVar(var):
            return subst.get(var, ty)
        case typed.TAp(arg, ret):
            return typed.TAp(apply_subst(subst, arg), apply_subst(subst, ret))
        case typed.TCon():
            return ty
        case _:
            raise TypeError(f"Cannot apply substitution to {ty=}")


def compose_subst(s1: Substitution, s2: Substitution) -> Substitution:
    next_subst_values = [apply_subst(s1, ty) for ty in s2.values()]
    next_subst = dict(zip(s2.keys(), next_subst_values)) | s1
    return next_subst


def apply_subst_scheme(subst: Substitution, scheme: Scheme) -> Scheme:
    subst = subst.copy()
    for var in scheme.vars:
        subst.pop(var, None)

    return Scheme(scheme.vars, apply_subst(subst, scheme.ty))


def apply_subst_ctx(subst: Substitution, ctx: Context) -> Context:
    for key in ctx.keys():
        ctx[key] = apply_subst_scheme(subst, ctx[key])
    return ctx



def free_type_vars(ty: typed.Type) -> set[int]:
    match ty:
        case typed.TVar(var):
            return {var}
        case typed.TAp(arg, ret):
            return free_type_vars(arg) | free_type_vars(ret)
        case typed.TCon():
            return set()
        case _:
            raise TypeError(f"Cannot free type vars from {ty=}")


def free_type_vars_scheme(scheme: Scheme):
    return free_type_vars(scheme.ty).difference(scheme.vars)


def free_type_vars_ctx(ctx: Context) -> set[int]:
    return set.union(*map(free_type_vars_scheme, ctx.values()), set())


def generalize(ctx: Context, ty: typed.Type) -> Scheme:
    """abstracts a type over all type variables which are free in the type but not free in the given type context"""
    vars = free_type_vars(ty).difference(free_type_vars_ctx(ctx))
    return Scheme(list(vars), ty)


