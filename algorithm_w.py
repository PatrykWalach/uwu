from __future__ import annotations
import itertools
import dataclasses
import functools
import typing
import terms
import typed
from util import ap


@dataclasses.dataclass
class Scheme:
    vars: list[int]
    t: typed.Type


Substitution: typing.TypeAlias = dict[int, typed.Type]
Context: typing.TypeAlias = dict[str, Scheme]  # dict[str, Scheme]

counter = 0


def fresh_ty_var() -> typed.Type:
    global counter
    counter += 1
    return typed.TVar(counter)


def apply_subst(subst: Substitution, ty: typed.Type) -> typed.Type:
    match ty:
        case typed.TNum() | typed.TStr():
            return ty
        case typed.TVar(var):
            return subst.get(var, typed.TVar(var))
        case typed.TGeneric(id, params):
            params = (apply_subst(subst, ty) for ty in params)
            return typed.TGeneric(id, tuple(params))
        case _:
            raise TypeError(f"Cannot apply substitution to {ty}")


def compose_subst(s1: Substitution, s2: Substitution) -> Substitution:
    next_subst = [apply_subst(s1, ty) for ty in s2.values()]
    next_subst = dict(zip(s2.keys(), next_subst)) | s1
    return next_subst

# T\x is remove x from T


def free_type_vars(type: typed.Type) -> set[int]:
    match type:
        case typed.TVar(var):
            return {var}
        case typed.TNum() | typed.TStr():
            return set()
        case typed.TGeneric(_, params):
            return functools.reduce(
                lambda acc, ty: acc | free_type_vars(ty),
                params,
                set())
        case _:
            raise TypeError(f"Cannot free type vars from {type}")


def free_type_vars_scheme(scheme: Scheme):
    return free_type_vars(scheme.t).difference(scheme.vars)


def free_type_vars_ctx(ctx: Context) -> set[int]:
    return set.union(*map(free_type_vars_scheme, ctx.values()), set())


def generalize(ctx: Context, ty: typed.Type) -> Scheme:
    """abstracts a type over all type variables which are free in the type but not free in the given type context"""
    vars = free_type_vars(ty).difference(free_type_vars_ctx(ctx))
    return Scheme(list(vars), ty)


def unify(a: typed.Type, b: typed.Type) -> Substitution:
    match (a, b):
        case (typed.TNum(), typed.TNum()) | (typed.TStr(), typed.TStr()):
            return {}
        case (typed.TGeneric(val0, params0), typed.TGeneric(val1, params1)) if val0 == val1 and len(params0) == len(params1):

            s1 = {}
            for param0, param1 in zip(params0, params1):
                s2 = unify(apply_subst(s1, param0),
                           apply_subst(s1, param1))
                s1 = compose_subst(s2, s1)

            return s1

        case (typed.TVar(u), t):
            return var_bind(u, t)
        case (t, typed.TVar(u)):
            return var_bind(u, t)
        case _:
            raise TypeError(f"Cannot unify {a} and {b}")


def var_bind(u: int, t: typed.Type) -> Substitution:
    match t:
        case typed.TVar(tvar2) if u == tvar2:
            return {}
        case typed.TVar(_):
            return {u: t}
        case t if u in free_type_vars(t):
            raise TypeError(f"circular use: {u} occurs in {t}"
                            )
        case t:
            return {u: t}


def apply_subst_scheme(subst: Substitution, scheme: Scheme) -> Scheme:
    subst = subst.copy()
    for var in scheme.vars:
        subst.pop(var, None)

    return Scheme(scheme.vars, apply_subst(
        subst, scheme.t))


def apply_subst_env(subst: Substitution, ctx: Context) -> Context:
    for key in ctx.keys():
        ctx[key] = apply_subst_scheme(subst, ctx[key])
    return ctx
    # return ctx
    # next_ctx = [apply_subst_scheme(subst, scheme) for scheme in ctx.values()]
    # next_ctx = dict(zip(ctx.keys(), next_ctx))
    # return next_ctx


def instantiate(scheme: Scheme) -> typed.Type:
    # newVars <- traverse (const newTyVar) vars
    # let subst = Map.fromList (zip vars newVars)
    # pure (applySubst subst ty)
    newVars = [fresh_ty_var() for _ in scheme.vars]
    subst = dict(zip(scheme.vars, newVars))
    return apply_subst(subst, scheme.t)


def unify_subst(a: typed.Type, b: typed.Type, subst: Substitution) -> Substitution:
    t = unify(a, b)
    return compose_subst(t, subst)


def infer(subst: Substitution, ctx: Context, exp: terms.AstTree) -> tuple[Substitution, typed.Type]:
    match exp:
        case terms.ELiteral(value=str()):
            return (subst, typed.TStr())
        case terms.ELiteral(value=float()):
            return (subst, typed.TNum())
        case terms.EIdentifier(var):
            return (subst, instantiate(ctx[var]))
        case terms.EProgram(body) | terms.EDo(body):
            ty = fresh_ty_var()
            ctx = ctx.copy()

            for exp in body:
                subst, ty = infer(subst, ctx, exp)

            return subst, ty
        case terms.EVariableDeclaration(terms.EIdentifier(id), init):
            subst, t1 = infer(subst, ctx, init)
            # tmp_t = generalize(subst,ctx, t1)
            ctx[id] = Scheme([], t1)  # tmp_t
            return subst, t1
        # case terms.BinaryExpr('++',left,right):
        #     s1,ctx,ty_left=apply_subst(left)
        #     s2,ctx,ty_right=apply_subst(right)
        #     return compose_subst(s2,s1), ctx, typed.string()
        case terms.EBinaryExpr('+' | '*' | '/' | '//' | '-', left, right):
            # ty = fresh_ty_var()
            subst, ty_left = infer(subst, ctx, left)
            subst = unify_subst(ty_left, typed.TNum(), subst)
            subst, ty_right = infer(subst, ctx, right)
            subst = unify_subst(ty_right, typed.TNum(), subst)
            # subst = unify_subst(ty, typed.TNum(), subst)

            # subst = unify_subst()

            return subst, typed.TNum()
        case terms.EParam(terms.EIdentifier(id), hint):
            ty1 = fresh_ty_var()
            ctx[id] = Scheme([], ty1)
            return {}, ty1
        case terms.ECall(id, args):
            ty_call = fresh_ty_var()
            subst, ty1 = infer(subst, ctx, id)
            params = tuple[typed.Type, ...]()
            for arg in args:
                subst, t = infer(subst, ctx, arg)
                params += (t,)

            subst = unify_subst(ty1, typed.TGeneric('Def', (
                typed.TGeneric('Params', params),
                ty_call
            )), subst)

            return subst, ty_call
        case terms.EDef(terms.EIdentifier(id), params, body):
            t_ctx = ctx.copy()

            ty_params = tuple[typed.Type, ...]()
            for param in params:
                subst, t1 = infer(subst, t_ctx, param)
                ty_params: tuple[typed.Type, ...] = (*ty_params, t1)

            ty1 = typed.TDef(tuple(ty_params), fresh_ty_var())
            t_ctx[id] = Scheme([], ty1)

            subst, ty_body = infer(subst, t_ctx, body)

            ty1 = typed.TDef(tuple(ty_params), ty_body)
            ctx[id] = Scheme([], ty1)

            return subst, ty1
        case _:
            raise TypeError(f"Cannot infer type of {exp=}")

        # case terms.Def(id,params):


def type_infer(ctx: Context, exp: terms.AstTree):
    s, t = infer({}, ctx, exp)
    return apply_subst(s, t)
