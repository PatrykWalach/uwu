from __future__ import annotations

import dataclasses
import functools
import typing

import case_tree
import terms
import typed

counter = 0


def fresh_ty_var(kind: typed.Kind=typed.KStar()) -> typed.TVar:
    global counter
    counter += 1
    return typed.TVar(counter, kind)





# T\x is remove x from T





class UnifyException(Exception):
    pass


class CircularUseException(Exception):
    pass

import Ctx

def unify(a: typed.Type, b: typed.Type) -> Ctx.Substitution:
    match (a, b):
        case (typed.TCon(), typed.TCon()) if a is b:
            return {}
        case (
            typed.TAp(arg0, ret0),
            typed.TAp(arg1, ret1),
        ):
            subst = unify_subst(arg0, arg1, {})
            subst = unify_subst(ret0, ret1, subst)

            return subst
        case (typed.TVar(u), t) | (t, typed.TVar(u)) if typed.kind(  # type:ignore[misc]
            a
        ) != typed.kind(b):
            raise UnifyException(f"Kind for {a=} and {b=} does not match")
        case (typed.TVar(u), t) | (t, typed.TVar(u)):  # type:ignore[misc]
            return var_bind(u, t)

    raise UnifyException(f"Cannot unify {a=} and {b=}")


def var_bind(u: int, t: typed.Type) -> Ctx.Substitution:
    match t:
        case typed.TVar(tvar2) if u == tvar2:
            return {}
        case typed.TVar(_):
            return {u: t}
        case t if u in Ctx.free_type_vars(t):
            raise CircularUseException(f"circular use: {u} occurs in {t}")

    return {u: t}



    # return ctx
    # next_ctx = [apply_subst_scheme(subst, scheme) for scheme in ctx.values()]
    # next_ctx = dict(zip(ctx.keys(), next_ctx))
    # return next_ctx




def instantiate(scheme: Ctx.Scheme) -> typed.Type:
    newVars: list[typed.Type] = [fresh_ty_var() for _ in scheme.vars]
    subst = dict(zip(scheme.vars, newVars))
    return Ctx.apply_subst(subst, scheme.ty)


def unify_subst(a: typed.Type, b: typed.Type, subst: Ctx.Substitution) -> Ctx.Substitution:
    t = unify(Ctx.apply_subst(subst, a), Ctx.apply_subst(subst, b))
    return Ctx.compose_subst(t, subst)

def reduce_args(ty_items: list[typed.Type], ty_call: typed.Type) -> typed.Type:
    return functools.reduce(
        flip(typed.TDef),
        ty_items or [typed.TUnit],
        ty_call,
    )



def infer(
    subst: Ctx.Substitution,
    ctx: Ctx.Context,
    node: terms.AstNode,
) -> tuple[Ctx.Substitution, typed.Type]:

    match node:
        case terms.EStrLiteral(value):
            return subst, typed.TStr
        case terms.ENumLiteral(value):
            return subst, typed.TNum
        case terms.EFloatLiteral(value):
            return subst, typed.TFloat
        case terms.EIdentifier(var):
            return subst, instantiate(ctx[var])
        case terms.EDo(block, hint):
            subst, ty_hint = infer(subst, ctx, hint)
            subst, ty = infer(subst, ctx, block)
            subst = unify_subst(ty, ty_hint, subst)

            return subst, ty
        case terms.EProgram(body, ctx):
            return infer(subst, ctx, terms.EBlock(body))
        case terms.EBlock(body):
            ty = typed.TUnit
            ctx = ctx.copy()

            for node in body:
                subst, ty = infer(subst, ctx, node)

            return subst, ty
        case terms.ELet(id, init, hint):
            subst, ty_init = infer(subst, ctx, init)
            subst, ty_hint = infer(subst, ctx, hint)
            subst = unify_subst(ty_init, ty_hint, subst)

            ctx[id] = Ctx.Scheme.from_subst(subst, ctx, ty_hint)

            return subst, ty_hint
        case terms.EExternal():
            return subst, fresh_ty_var()

        case terms.EEnumDeclaration(id, generics=generics, variants=variants):
            # option_con = TCon('Option', KFun(KStar(),KStar()))
            # ty = TAp<option_con, var1>
            # ty_variant_con = TCon('Some', KFun(KStar(),KStar()))
            # ty_variant = TAp<ty_var_con, var1>
            # ty_con = ty_variant -> ty

            t_ctx = ctx.copy()

            ty_generics = list[typed.Type]()

            for generic in generics:

                ty_generic = fresh_ty_var()
                t_ctx[generic.name] = Ctx.Scheme([], ty_generic)
                ty_generics.append(ty_generic)

            ty_kind = functools.reduce(
                flip(typed.KFun),
                map(typed.kind, ty_generics),
                typed.KStar().w(),
            )

            ty_con = typed.TCon(id, ty_kind, [variant.id for variant in variants]).w()

            ty = functools.reduce(typed.TAp, ty_generics, ty_con)

            for variant in variants:
                ty_fields = list[typed.Type]()

                for field in variant.fields:
                    subst, ty_field = infer(subst, t_ctx, field)
                    ty_fields.append(ty_field)

                ty_variant_co_kind = functools.reduce(
                    flip(typed.KFun),
                    map(typed.kind, ty_fields),
                    typed.KStar().w(),
                )
                ty_variant_con = typed.TCon(variant.id, ty_variant_co_kind).w()
                ty_variant = functools.reduce(typed.TAp, ty_fields, ty_variant_con)

                ctx["$" + variant.id] = Ctx.Scheme.from_subst(subst, ctx, ty_variant_con)
                ctx[variant.id] = Ctx.Scheme.from_subst(
                    subst, ctx, typed.TDef(ty_variant, ty)
                )

            ctx[id] = Ctx.Scheme.from_subst(subst, ctx, ty_con)

            return subst, typed.TUnit
        case terms.EUnaryExpr(op, expr):
            match op:
                case "-" | "+":
                    subst, ty_expr = infer(subst, ctx, expr)
                    subst = unify_subst(ty_expr, typed.TNum, subst)
                    return subst, typed.TNum
                case ("not"):
                    subst, ty_expr = infer(subst, ctx, expr)
                    subst = unify_subst(ty_expr, typed.TBool, subst)
                    return subst, typed.TBool
                case ("!"):
                    subst, ty_expr = infer(subst, ctx, expr)
                    return subst, typed.TBool
                case op:
                    typed.assert_never(op)
        case terms.EBinaryExpr(op, left, right):
            subst, ty_op = infer(subst, ctx, terms.EIdentifier(op))
            subst, ty_left = infer(subst, ctx, left)
            subst, ty_right = infer(subst, ctx, right)
            ty_ret = fresh_ty_var()

            subst = unify_subst(
                ty_op, typed.TDef(ty_left, typed.TDef(ty_right, ty_ret)), subst
            )

            return subst, ty_ret
        case terms.EMatchAs(id):
            ty = fresh_ty_var()
            ctx[id] = Ctx.Scheme([], ty)
            return subst, ty
        case terms.EParam(id, hint):
            subst, ty = infer(subst, ctx, hint)
            ctx[id] = Ctx.Scheme([], ty)
            return subst, ty
        case terms.EVariantCall(id, args):
            # option_con = TCon('Option', KFun(KStar(),KStar()))
            # ty = TAp<option_con, var1>
            # ty_variant_con = TCon('Some', KFun(KStar(),KStar()))
            # ty_variant = TAp<ty_var_con, var1>
            # ty_con = ty_variant -> ty
            ty = fresh_ty_var()
            subst, ty_con = infer(subst, ctx, terms.EIdentifier(id))

            ty_args = list[typed.Type]()

            for arg in args:
                subst, ty_arg = infer(subst, ctx, arg)
                ty_args.append(ty_arg)

            kind_variant = functools.reduce(
                flip(typed.KFun), map(typed.kind, ty_args), typed.KStar().w()
            )

            subst, ty_variant_con = infer(subst, ctx, terms.EIdentifier("$" + id))

            ty_variant = functools.reduce(
                typed.TAp,
                ty_args,
                ty_variant_con,
            )

            subst = unify_subst(ty_con, typed.TDef(ty_variant, ty), subst)

            return subst, ty
        case terms.ECall(fn, args):
            subst, ty_fn = infer(subst, ctx, fn)

            ty_args = list[typed.Type]()

            for arg in reversed(args):
                subst, ty_arg = infer(subst, ctx, arg)
                ty_args.append(ty_arg)

            ty = fresh_ty_var()
            subst = unify_subst(ty_fn, reduce_args(ty_args, ty), subst)

            return subst, ty

        case terms.EMaybeOrElse(value) | terms.EMaybeHint(value) | terms.EExpr(value):
            return infer(subst, ctx, value)
        case terms.EBinaryOpDef(id, params, body, hint, generics) | terms.EDef(
            id, params, body, hint, generics
        ):
            t_ctx = ctx.copy()

            for generic in generics:
                ty_generic = fresh_ty_var()
                t_ctx[generic.name] = Ctx.Scheme([], ty_generic)

            subst, ty_hint = infer(subst, t_ctx, hint)

            ty_params = list[typed.Type]()

            for param in reversed(params):
                subst, ty_param = infer(subst, t_ctx, param)
                ty_params.append(ty_param)

            ty = reduce_args(ty_params, ty_hint)

            #
            subst, ty_body = infer(subst, t_ctx, body)

            subst = unify_subst(ty_body, ty_hint, subst)

            ctx[id] = Ctx.Scheme.from_subst(subst, ctx, ty)

            return subst, ty
        case terms.EIf(test, then, or_else, hint=hint):

            subst, ty_hint = infer(subst, ctx, hint)
            subst, ty_condition = infer(subst, ctx, test)
            subst = unify_subst(ty_condition, typed.TBool, subst)

            subst, ty_then = infer(subst, ctx, then)
            subst = unify_subst(ty_then, ty_hint, subst)

            subst, ty_or_else = infer(subst, ctx, or_else)
            subst = unify_subst(ty_or_else, ty_hint, subst)

            return subst, ty_hint
        case terms.EMaybeOrElseNothing():
            return subst, typed.TUnit
        case terms.EMaybeHintNothing():
            return subst, fresh_ty_var()

        case terms.EHint(id, args):
            subst, ty_con = infer(subst, ctx, terms.EIdentifier(id))

            ty_args = list[typed.Type]()
            for hint_arg in args:
                subst, ty = infer(subst, ctx, hint_arg)
                ty_args.append(ty)

            ty = fresh_ty_var()
            subst = unify_subst(
                functools.reduce(typed.TAp, ty_args, ty_con),
                ty,
                subst,
            )

            return subst, ty
        case terms.ECaseOf(expr, cases=cases):

            subst, ty_expr = infer(subst, ctx, expr)
            ctx["$"] = Ctx.Scheme.from_subst(subst, ctx, ty_expr)

            tree = case_tree.gen_match(cases)

            subst, ty = infer_case_tree(subst, ctx, tree)

            return subst, ty

        case terms.EArray(args):
            ty = fresh_ty_var()
            for arg in args:
                subst, ty1 = infer(subst, ctx, arg)
                subst = unify_subst(ty1, ty, subst)

            return subst, typed.TArray(ty)

        case terms.EInter(_, mid, right):
            subst, ty1 = infer(subst, ctx, mid)
            subst = unify_subst(ty1, typed.TStr, subst)
            subst, ty2 = infer(subst, ctx, right)
            subst = unify_subst(ty2, typed.TStr, subst)

            return subst, typed.TStr

        case terms.EInterOrStr(expr):
            subst, ty1 = infer(subst, ctx, expr)
            subst = unify_subst(ty1, typed.TStr, subst)

            return subst, typed.TStr
        case node:
            typed.assert_never(node)


def type_infer(ctx: Ctx.Context, node: terms.AstNode) -> typed.Type:
    s, t = infer({}, ctx, node)
    return Ctx.apply_subst(s, t)


# def scheme_from_type(subst: Substitution, ctx: Context, ty: typed.Type):
# ftv = ftv = free_type_vars(apply_subst(
#     subst, ty)).difference(free_type_vars_ctx(apply_subst_ctx(subst, ctx)))

# return Scheme(list(ftv), ty)


class NonExhaustiveMatchException(Exception):
    pass


A = typing.TypeVar("A")
B = typing.TypeVar("B")
C = typing.TypeVar("C")


def flip(fn: typing.Callable[[B, C], A]) -> typing.Callable[[C, B], A]:
    return functools.wraps(fn)(lambda *args: fn(*args[::-1]))


def alternatives(ty: typed.Type) -> list[str]:
    match ty:
        case typed.TCon(alts=alts):
            return alts
        case typed.TAp(con=con, arg=arg):
            return alternatives(con) + alternatives(arg)
        case _:
            return []


def infer_case_tree(
    subst: Ctx.Substitution,
    ctx: Ctx.Context,
    tree: case_tree.CaseTree,
    o_alts: dict[str, list[str]] | None = None,
) -> tuple[Ctx.Substitution, typed.Type]:
    alts = o_alts or {}

    match tree:
        case case_tree.MissingLeaf():
            if any(alts.values()):
                raise NonExhaustiveMatchException()
            return subst, fresh_ty_var()
        case case_tree.Node(var, pattern_name, vars, yes, no):

            subst, ty_var = infer(subst, ctx, terms.EIdentifier(var))  # x | x.0
            subst, ty_pattern_name = infer(
                subst, ctx, terms.EIdentifier(pattern_name)
            )  # Some() | None()
            t_ctx = ctx.copy()

            # exhaustive
            if var not in alts:
                alts[var] = alternatives(ty_pattern_name)

            if pattern_name in alts[var]:
                alts[var].remove(pattern_name)

            ty_vars = list[typed.Type](fresh_ty_var() for _ in vars)

            subst, pattern_name_con = infer(
                subst, ctx, terms.EIdentifier("$" + pattern_name)
            )

            subst = unify_subst(
                ty_pattern_name,
                typed.TDef(
                    functools.reduce(
                        typed.TAp,
                        ty_vars,
                        pattern_name_con,
                    ),
                    ty_var,
                ),
                subst,
            )

            for var2, ty_var in zip(vars, ty_vars):
                t_ctx[var2] = Ctx.Scheme.from_subst(subst, t_ctx, ty_var)

            # subst return type
            ty = fresh_ty_var()

            subst, ty_yes = infer_case_tree(
                subst,
                t_ctx,
                yes,
                {key: value for key, value in alts.items() if key != var}
                | {var2: alternatives(t_ctx[var2].ty) for var2 in vars},
            )
            subst = unify_subst(ty_yes, ty, subst)

            subst, ty_no = infer_case_tree(subst, ctx, no, alts)
            subst = unify_subst(ty_no, ty, subst)

            return subst, ty
        case case_tree.Leaf(do):
            subst, ty_do = infer(subst, ctx, do)

            return subst, ty_do

    raise TypeError(f"Unsupported case tree {tree}")


Variants: typing.TypeAlias = dict[str, frozenset[str]]
