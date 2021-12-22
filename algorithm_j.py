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
        case terms.EDo(body, hint) if hint != None:
            subst, hint = infer(subst, ctx, hint)
            ty = fresh_ty_var()
            ctx = ctx.copy()

            for exp in body:
                subst, ty = infer(subst, ctx, exp)

            subst = unify_subst(ty, hint, subst)

            return subst, hint
        case terms.EProgram(body) | terms.EDo(body) | terms.EBlockStmt(body):
            ty = typed.TUnit()
            ctx = ctx.copy()

            for exp in body:
                subst, ty = infer(subst, ctx, exp)

            return subst, ty
        case terms.EVariableDeclaration(
            terms.EIdentifier(id), init, hint
        ) if hint != None:
            subst, hint = infer(subst, ctx, hint)
            subst, t1 = infer(subst, ctx, init)
            subst = unify_subst(t1, hint, subst)

            ctx[id] = Scheme.from_subst(subst, ctx, hint)

            return subst, hint
        case terms.EVariableDeclaration(terms.EIdentifier(id), init, hint=None):
            subst, t1 = infer(subst, ctx, init)

            ctx[id] = Scheme.from_subst(subst, ctx, t1)
            return subst, t1
        # case terms.EFieldsUnnamed(unnamed):
        #     types = list[typed.Type]()
        #     for field in unnamed:
        #         subst, ty = infer(subst, ctx, field)
        #         types.append(ty)

        #     return subst, typed.TGeneric(TFieldsMeta, types)
        # case terms.EVariant(terms.EIdentifier(id), fields):
        #     subst, ty = infer(subst, ctx, fields)
        #     ctx[id] = Scheme.from_subst(subst, ctx, ty)
        #     return subst, ty
        case terms.EEnumDeclaration(terms.EIdentifier(id), generics, variants=variants):

            t_ctx = ctx.copy()

            for generic in generics:
                t_ctx[generic.name] = Scheme([], fresh_ty_var())

            for variant in variants:

                types = typed.TGeneric(
                    id, [t_ctx[generic.name].ty for generic in generics]
                )

                for field in reversed(variant.fields.unnamed):
                    subst, ty = infer(subst, t_ctx, field)
                    types = typed.TDef(ty, types)

                if not variant.fields.unnamed:
                    types = typed.TThunk(types)

                ctx[variant.id.name] = Scheme.from_subst(subst, t_ctx, types)

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
        case terms.EParam(terms.EIdentifier(id), hint) if hint != None:
            subst, hint = infer(subst, ctx, hint)
            ctx[id] = Scheme.from_subst(subst, ctx, hint)
            return subst, hint
        case terms.EParam(terms.EIdentifier(id), hint=None) | terms.EParamPattern(
            terms.EIdentifier(id)
        ):
            ty = fresh_ty_var()
            # ctx[id] = Scheme.from_subst(subst, ctx, ty)
            ctx[id] = Scheme([], ty)
            return subst, ty
        case terms.ECall(id, []):
            ty = fresh_ty_var()
            subst, ty1 = infer(subst, ctx, id)

            subst = unify_subst(ty1, typed.TThunk(ty), subst)

            return subst, ty
        case terms.ECall(id, args):
            ty = fresh_ty_var()
            subst, ty1 = infer(subst, ctx, id)

            ty_call = ty

            for arg in reversed(args):
                subst, ty_arg = infer(subst, ctx, arg)
                ty_call = typed.TDef(ty_arg, ty_call)

            subst = unify_subst(ty1, ty_call, subst)

            return subst, ty
        case terms.EDef(terms.EIdentifier(id), [], body, hint) if hint != None:
            subst, hint = infer(subst, ctx, hint)
            t_ctx = ctx.copy()

            ty1 = typed.TThunk(hint)
            ctx[id] = Scheme.from_subst(subst, ctx, ty1)

            subst, ty_body = infer(subst, t_ctx, body)
            subst = unify_subst(ty_body, hint, subst)

            return subst, ty1
        case terms.EDef(terms.EIdentifier(id), [], body, hint=None):
            t_ctx = ctx.copy()

            ty1 = typed.TThunk(fresh_ty_var())
            t_ctx[id] = Scheme.from_subst(subst, ctx, ty1)

            subst, ty_body = infer(subst, t_ctx, body)

            ty1 = typed.TThunk(ty_body)

            ctx[id] = Scheme.from_subst(subst, ctx, ty1)

            return subst, ty1
        case terms.EDef(terms.EIdentifier(id), params, body, hint) if hint != None:
            subst, hint = infer(subst, ctx, hint)
            t_ctx = ctx.copy()

            ty = hint
            for param in reversed(params):
                subst, t1 = infer(subst, t_ctx, param)
                ty = typed.TDef(t1, ty)

            ctx[id] = Scheme.from_subst(subst, ctx, ty)

            subst, ty_body = infer(subst, t_ctx, body)
            subst = unify_subst(ty_body, hint, subst)

            return subst, ty
        case terms.EDef(terms.EIdentifier(id), params, body, hint=None):
            t_ctx = ctx.copy()

            hint = fresh_ty_var()
            ty = hint
            for param in reversed(params):
                subst, t1 = infer(subst, t_ctx, param)
                ty = typed.TDef(t1, ty)

            t_ctx[id] = Scheme.from_subst(subst, ctx, ty)

            subst, ty_body = infer(subst, t_ctx, body)
            subst = unify_subst(ty_body, hint, subst)

            ctx[id] = Scheme.from_subst(subst, ctx, ty)

            return subst, ty
        case terms.EIf(test, then, or_else=None, hint=None):
            subst, ty_condition = infer(subst, ctx, test)
            subst = unify_subst(ty_condition, typed.TBool(), subst)

            subst, ty_then = infer(subst, ctx, then)
            unify_subst(ty_then, typed.TOption(fresh_ty_var()), subst)

            return subst, ty_then

        case terms.EIf(test, then, or_else, hint=None) if or_else != None:
            subst, ty_condition = infer(subst, ctx, test)
            subst = unify_subst(ty_condition, typed.TBool(), subst)

            subst, ty_then = infer(subst, ctx, then)

            subst, ty_or_else = infer(subst, ctx, or_else)
            subst = unify_subst(ty_or_else, ty_then, subst)

            return subst, ty_then
        case terms.EIf(test, then, or_else=None, hint=hint) if hint != None:
            subst, hint = infer(subst, ctx, hint)
            subst = unify_subst(hint, typed.TOption(fresh_ty_var()), subst)

            subst, ty_condition = infer(subst, ctx, test)
            subst = unify_subst(ty_condition, typed.TBool(), subst)

            subst, ty_then = infer(subst, ctx, then)
            subst = unify_subst(ty_then, hint, subst)

            return subst, hint
        case terms.EIf(
            test, then, or_else, hint=hint
        ) if or_else != None and hint != None:
            subst, hint = infer(subst, ctx, hint)
            subst, ty_condition = infer(subst, ctx, test)
            subst = unify_subst(ty_condition, typed.TBool(), subst)

            subst, ty_then = infer(subst, ctx, then)
            subst = unify_subst(ty_then, hint, subst)

            subst, ty_or_else = infer(subst, ctx, or_else)
            subst = unify_subst(ty_or_else, hint, subst)

            return subst, hint
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
        case terms.EEnumPattern(id, []):
            ty = fresh_ty_var()
            subst, ty_id = infer(subst, ctx, id)
            subst = unify_subst(ty_id, typed.TThunk(ty), subst)
            return subst, ty
        case terms.EEnumPattern(id, patterns):
            ty = fresh_ty_var()
            subst, ty_id = infer(subst, ctx, id)

            ty_call = ty
            for pattern in reversed(patterns):
                subst, ty_pattern = infer(subst, ctx, pattern)
                ty_call = typed.TDef(ty_pattern, ty_call)

            subst = unify_subst(ty_id, ty_call, subst)
            return subst, ty
        case terms.EArray(args):
            ty = fresh_ty_var()
            for arg in args:
                subst, ty1 = infer(subst, ctx, arg)
                subst = unify_subst(ty1, ty, subst)

            return subst, typed.TArray(ty)
        case terms.EArrayPattern(first, rest=None):
            ty = fresh_ty_var()

            for element in first:
                subst, ty1 = infer(subst, ctx, element)
                subst = unify_subst(ty1, ty, subst)

            return subst, typed.TArray(ty)
        case terms.EArrayPattern(first, rest) if rest != None:
            ty = fresh_ty_var()

            for element in first:
                subst, ty1 = infer(subst, ctx, element)
                subst = unify_subst(ty1, ty, subst)

            subst, ty1 = infer(subst, ctx, rest)
            subst = unify_subst(ty1, typed.TArray(ty), subst)

            return subst, typed.TArray(ty)
        case terms.ESpread(terms.EIdentifier(id), last):
            ty = fresh_ty_var()

            for element in last:
                subst, ty1 = infer(subst, ctx, element)
                subst = unify_subst(ty1, ty, subst)

            ctx[id] = Scheme.from_subst(subst, ctx, typed.TArray(ty))

            return subst, typed.TArray(ty)
        case _:
            raise TypeError(f"Cannot infer type of {exp=}")

        # case terms.Def(id,params):


def type_infer(ctx: Context, exp: terms.AstTree):
    s, t = infer({}, ctx, exp)
    return apply_subst(s, t)


# def scheme_from_type(subst: Substitution, ctx: Context, ty: typed.Type):
# ftv = ftv = free_type_vars(apply_subst(
#     subst, ty)).difference(free_type_vars_ctx(apply_subst_ctx(subst, ctx)))

# return Scheme(list(ftv), ty)
