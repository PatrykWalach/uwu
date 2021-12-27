from __future__ import annotations
import logging
import itertools
import dataclasses
import functools
import typing
import terms
import typed


@dataclasses.dataclass
class Scheme:
    vars: list[int]
    ty: typed.Type

    @staticmethod
    def from_subst(subst: Substitution, ctx: Context, ty1: typed.Type):
        ftv = free_type_vars(apply_subst(subst, ty1))
        ftv -= free_type_vars_ctx(apply_subst_ctx(subst, ctx))

        return Scheme(list(ftv), apply_subst(subst, ty1))


Substitution: typing.TypeAlias = dict[int, typed.Type]
Context: typing.TypeAlias = dict[str, Scheme]  # dict[str, Scheme]

counter = 0


def fresh_ty_var() -> typed.TVar:
    global counter
    counter += 1
    return typed.TVar(counter)


def apply_subst(subst: Substitution, ty: typed.Type) -> typed.Type:
    match ty:
        # case typed.TNum() | typed.TStr():
        #     return ty
        case typed.TVar(var):
            return subst.get(var, typed.TVar(var))
        case typed.TGeneric(id, params):
            params = [apply_subst(subst, ty) for ty in params]
            return typed.TGeneric(id, params)
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
        # case typed.TNum() | typed.TStr():
        #     return set()
        case typed.TGeneric(_, params):
            return functools.reduce(
                lambda acc, ty: acc | free_type_vars(ty), params, set()
            )
        case _:
            raise TypeError(f"Cannot free type vars from {type}")


def free_type_vars_scheme(scheme: Scheme):
    return free_type_vars(scheme.ty).difference(scheme.vars)


def free_type_vars_ctx(ctx: Context) -> set[int]:
    return set.union(*map(free_type_vars_scheme, ctx.values()), set())


def generalize(ctx: Context, ty: typed.Type) -> Scheme:
    """abstracts a type over all type variables which are free in the type but not free in the given type context"""
    vars = free_type_vars(ty).difference(free_type_vars_ctx(ctx))
    return Scheme(list(vars), ty)


class UnifyException(Exception):
    pass


def unify(a: typed.Type, b: typed.Type) -> Substitution:
    match (a, b):
        # case (typed.TNum(), typed.TNum()) | (typed.TStr(), typed.TStr()):
        #     return {}
        case (
            typed.TGeneric(val0, params0),
            typed.TGeneric(val1, params1),
        ) if val0 == val1 and len(params0) == len(params1):

            s1 = {}

            for param0, param1 in zip(params0, params1):
                s2 = unify(apply_subst(s1, param0), apply_subst(s1, param1))
                s1 = compose_subst(s2, s1)

            return s1
        case (typed.TVar(u), t) | (t, typed.TVar(u)):
            return var_bind(u, t)
        case _:
            raise UnifyException(f"Cannot unify {a=} and {b=}")


def var_bind(u: int, t: typed.Type) -> Substitution:
    match t:
        case typed.TVar(tvar2) if u == tvar2:
            return {}
        case typed.TVar(_):
            return {u: t}
        case t if u in free_type_vars(t):
            raise TypeError(f"circular use: {u} occurs in {t}")
        case t:
            return {u: t}


def apply_subst_scheme(subst: Substitution, scheme: Scheme) -> Scheme:
    subst = subst.copy()
    for var in scheme.vars:
        subst.pop(var, None)

    return Scheme(scheme.vars, apply_subst(subst, scheme.ty))


def apply_subst_ctx(subst: Substitution, ctx: Context) -> Context:
    for key in ctx.keys():
        ctx[key] = apply_subst_scheme(subst, ctx[key])
    return ctx
    # return ctx
    # next_ctx = [apply_subst_scheme(subst, scheme) for scheme in ctx.values()]
    # next_ctx = dict(zip(ctx.keys(), next_ctx))
    # return next_ctx


def instantiate(scheme: Scheme) -> typed.Type:
    newVars: list[typed.Type] = [fresh_ty_var() for _ in scheme.vars]
    subst = dict(zip(scheme.vars, newVars))
    return apply_subst(subst, scheme.ty)


def unify_subst(a: typed.Type, b: typed.Type, subst: Substitution) -> Substitution:
    t = unify(apply_subst(subst, a), apply_subst(subst, b))
    return compose_subst(t, subst)


def reduce_ty_call(ty_items, ty_call):
    return functools.reduce(
        lambda ty_call, ty_item: typed.TDef(ty_item, ty_call),
        ty_items or [typed.TUnit()],
        ty_call,
    )


def infer(
    subst: Substitution, ctx: Context, exp: terms.AstTree
) -> tuple[Substitution, typed.Type]:
    match exp:
        case terms.ELiteral(value=str()):
            return subst, typed.TStr()
        case terms.ELiteral(value=float()):
            return subst, typed.TNum()
        case terms.EIdentifier(var):
            return subst, instantiate(ctx[var])
        case terms.EDo(body, hint):
            subst, hint = infer(subst, ctx, hint)
            ty = typed.TUnit()
            ctx = ctx.copy()

            for exp in body:
                subst, ty = infer(subst, ctx, exp)

            subst = unify_subst(ty, hint, subst)

            return subst, hint
        case terms.EProgram(body) | terms.EBlockStmt(body):
            ty = typed.TUnit()
            ctx = ctx.copy()

            for exp in body:
                subst, ty = infer(subst, ctx, exp)

            return subst, ty
        case terms.EVariableDeclaration(terms.EIdentifier(id), init, hint):
            subst, hint = infer(subst, ctx, hint)
            subst, t1 = infer(subst, ctx, init)
            subst = unify_subst(t1, hint, subst)

            ctx[id] = Scheme.from_subst(subst, ctx, hint)

            return subst, hint
        case terms.EEnumDeclaration(terms.EIdentifier(id), generics, variants=variants):

            t_ctx = ctx.copy()

            for generic in generics:
                t_ctx[generic.name] = Scheme([], fresh_ty_var())

            for variant in variants:

                ty = typed.TGeneric(
                    id, [instantiate(t_ctx[generic.name]) for generic in generics]
                )

                ty_fields = list[typed.Type]()

                for field in reversed(variant.fields.unnamed):
                    subst, ty_field = infer(subst, t_ctx, field)
                    ty_fields.append(ty_field)

                ty = reduce_ty_call(ty_fields, ty)

                ctx[variant.id.name] = Scheme.from_subst(subst, t_ctx, ty)

            ty = typed.TGeneric(id, [fresh_ty_var() for _ in generics])
            ctx[id] = Scheme([], ty)

            return subst, ty
        case terms.EBinaryExpr("+" | "*" | "/" | "//" | "-", left, right):
            subst, ty_left = infer(subst, ctx, left)
            subst = unify_subst(ty_left, typed.TNum(), subst)
            subst, ty_right = infer(subst, ctx, right)
            subst = unify_subst(ty_right, typed.TNum(), subst)
            return subst, typed.TNum()
        case terms.EBinaryExpr(">" | "<" | "<=" | ">=", left, right):
            subst, ty_left = infer(subst, ctx, left)
            subst = unify_subst(ty_left, typed.TNum(), subst)
            subst, ty_right = infer(subst, ctx, right)
            subst = unify_subst(ty_right, typed.TNum(), subst)
            return subst, typed.TBool()
        case terms.EMatchAs(terms.EIdentifier(id)):
            ty = fresh_ty_var()
            ctx[id] = Scheme([], ty)
            return subst, ty
        case terms.EParam(terms.EIdentifier(id), hint):
            subst, hint = infer(subst, ctx, hint)
            ctx[id] = Scheme([], hint)
            return subst, hint
        case terms.ECall(id, args):
            ty = fresh_ty_var()
            subst, ty_id = infer(subst, ctx, id)

            ty_args = list[typed.Type]()

            for arg in reversed(args):
                subst, ty_arg = infer(subst, ctx, arg)
                ty_args.append(ty_arg)

            ty_call = reduce_ty_call(ty_args, ty)

            subst = unify_subst(ty_id, ty_call, subst)

            return subst, ty
        case terms.EDef(terms.EIdentifier(id), params, body, hint):
            subst, hint = infer(subst, ctx, hint)
            t_ctx = ctx.copy()

            ty_params = list[typed.Type]()

            for param in reversed(params):
                subst, ty_param = infer(subst, t_ctx, param)
                ty_params.append(ty_param)

            ty = reduce_ty_call(ty_params, hint)

            t_ctx[id] = Scheme.from_subst(subst, t_ctx, ty)
            subst, ty_body = infer(subst, t_ctx, body)

            subst = unify_subst(ty_body, hint, subst)

            ctx[id] = Scheme.from_subst(subst, ctx, ty)

            return subst, ty
        case terms.EIf(test, then, or_else, hint=hint):

            subst, hint = infer(subst, ctx, hint)
            subst, ty_condition = infer(subst, ctx, test)
            subst = unify_subst(ty_condition, typed.TBool(), subst)

            subst, ty_then = infer(subst, ctx, then)
            subst = unify_subst(ty_then, hint, subst)

            subst, ty_or_else = infer(subst, ctx, or_else)
            subst = unify_subst(ty_or_else, hint, subst)

            return subst, hint
        case terms.EIfNone():
            return subst, typed.TOption(fresh_ty_var())
        case terms.EHintNone():
            return subst, fresh_ty_var()
        case terms.EHint(terms.EIdentifier(id), arguments):
            types = list[typed.Type]()
            for arg in arguments:
                subst, ty = infer(subst, ctx, arg)
                types.append(ty)

            subst, ty1 = infer(subst, ctx, terms.EIdentifier(id))
            subst = unify_subst(ty1, typed.TGeneric(id, types), subst)

            return subst, typed.TGeneric(id, types)
        case terms.ECaseOf(of, cases):
            ty1 = fresh_ty_var()

            subst, ty_of = infer(subst, ctx, of)

            for case in cases:
                ctx = ctx.copy()
                subst, ty2 = infer(subst, ctx, case)
                subst = unify_subst(ty2, typed.TDef(ty_of, ty1), subst)

            return subst, ty1
        case terms.ECase(pattern, body):
            subst, ty_pattern = infer(subst, ctx, pattern)
            subst, ty_body = infer(subst, ctx, body)
            return subst, typed.TDef(ty_pattern, ty_body)
        case terms.EEnumPattern(id, patterns):
            ty = fresh_ty_var()
            subst, ty_id = infer(subst, ctx, id)

            ty_patterns = list[typed.Type]()

            for pattern in reversed(patterns):
                subst, ty_pattern = infer(subst, ctx, pattern)
                ty_patterns.append(ty_pattern)

            ty_call = reduce_ty_call(
                ty_patterns,
                ty,
            )

            subst = unify_subst(ty_id, ty_call, subst)
            return subst, ty
        case terms.EArray(args):
            ty = fresh_ty_var()
            for arg in args:
                subst, ty1 = infer(subst, ctx, arg)
                subst = unify_subst(ty1, ty, subst)

            return subst, typed.TArray(ty)
        case terms.EMatchArray(patterns):
            ty = fresh_ty_var()

            for pattern in patterns:
                subst, ty1 = infer(subst, ctx, pattern)
                subst = unify_subst(ty1, ty, subst)

            return subst, typed.TArray(ty)
        
        case terms.EMatchTuple(patterns):
            ty_patterns =  list[typed.Type]()

            for pattern in patterns:
                subst, ty1 = infer(subst, ctx, pattern)
                ty_patterns.append(ty1)

            return subst, typed.TTuple(ty_patterns)
        case terms.ETuple(exprs):
            ty_exprs =  list[typed.Type]()

            for expr in exprs:
                subst, ty1 = infer(subst, ctx, expr)
                ty_exprs.append(ty1)

            return subst, typed.TTuple(ty_exprs)
        case _:
            raise TypeError(f"Cannot infer type of {exp=}")


def type_infer(ctx: Context, exp: terms.AstTree):
    s, t = infer({}, ctx, exp)
    return apply_subst(s, t)


# def scheme_from_type(subst: Substitution, ctx: Context, ty: typed.Type):
# ftv = ftv = free_type_vars(apply_subst(
#     subst, ty)).difference(free_type_vars_ctx(apply_subst_ctx(subst, ctx)))

# return Scheme(list(ftv), ty)
