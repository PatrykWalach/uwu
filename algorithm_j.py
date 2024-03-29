from __future__ import annotations

import dataclasses
import functools
import itertools
import typing

import case_tree
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


@dataclasses.dataclass
class Context:
    vars: dict[str, Scheme] = dataclasses.field(default_factory=dict)
    types: dict[str, Scheme] = dataclasses.field(default_factory=dict)



    def values(self) -> typing.Iterator[Scheme]:
        return itertools.chain(self.vars.values(), self.types.values())

    def copy(self) -> Context:
        return Context(self.vars.copy(), self.types.copy())


counter = 0


def fresh_ty_var(kind=typed.KStar()) -> typed.TVar:
    global counter
    counter += 1
    return typed.TVar(counter, kind)


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


# T\x is remove x from T


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


class UnifyException(Exception):
    pass


class CircularUseException(Exception):
    pass


def unify(a: typed.Type, b: typed.Type) -> Substitution:
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


def var_bind(u: int, t: typed.Type) -> Substitution:
    match t:
        case typed.TVar(tvar2) if u == tvar2:
            return {}
        case typed.TVar(_):
            return {u: t}
        case t if u in free_type_vars(t):
            raise CircularUseException(f"circular use: {u} occurs in {t}")

    return {u: t}


def apply_subst_scheme(subst: Substitution, scheme: Scheme) -> Scheme:
    subst = subst.copy()
    for var in scheme.vars:
        subst.pop(var, None)

    return Scheme(scheme.vars, apply_subst(subst, scheme.ty))


def apply_subst_ctx(subst: Substitution, ctx: Context) -> Context:
    for key, value in ctx.vars.items():
        ctx.vars[key] = apply_subst_scheme(subst, value)

    for key, value in ctx.types.items():
        ctx.types[key] = apply_subst_scheme(subst, value)

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


def reduce_args(ty_items: list[typed.Type], ty_call: typed.Type) -> typed.Type:
    return functools.reduce(
        flip(typed.TDef),
        ty_items or [typed.TUnit],
        ty_call,
    )


Inferable = (
    terms.EIdentifier
    | terms.EExpr
    | terms.EParam
    | terms.EUnaryExpr
    | terms.MaybeOrElse
    | terms.EProgram
    | terms.EVariantCall
    | terms.ELet
    | terms.EArray
    | terms.EBinaryExpr
    | terms.EBlock
    | terms.ECall
    | terms.ECaseOf
    | terms.EDef
    | terms.EDo
    | terms.EEnumDeclaration
    | terms.EExpr
    | terms.EExternal
    | terms.MaybeEHint
    | terms.EIf
    | terms.EBinaryOpDef
    | terms.EHint
    | terms.MaybeOrElseNothing
    | terms.EStrLiteral
    | terms.ENumLiteral
    | terms.EFloatLiteral
    | terms.MaybeEHintNothing
    | terms.ETypeIdentifier
)


def infer(
    subst: Substitution,
    ctx: Context,
    node: Inferable,
) -> tuple[Substitution, typed.Type]:
    match node:
        case terms.EStrLiteral(value):
            return subst, typed.TStr
        case terms.ENumLiteral(value):
            return subst, typed.TNum
        case terms.EFloatLiteral(value):
            return subst, typed.TFloat
        case terms.EIdentifier(var):
            return subst, instantiate(ctx.vars[var])
        case terms.ETypeIdentifier(var):
            return subst, instantiate(ctx.types[var])
        case terms.EDo(block, hint):
            subst, ty_hint = infer(subst, ctx, hint)
            subst, ty = infer(subst, ctx, block)
            subst = unify_subst(ty, ty_hint, subst)

            return subst, ty
        case terms.EProgram(body) | terms.EBlock(body):
            ty = typed.TUnit
            ctx = ctx.copy()

            for node in body:
                subst, ty = infer(subst, ctx, node)

            return subst, ty
        case terms.ELet(id, init, hint):
            subst, ty_init = infer(subst, ctx, init)
            subst, ty_hint = infer(subst, ctx, hint)
            subst = unify_subst(ty_init, ty_hint, subst)

            ctx.vars[id] = Scheme.from_subst(subst, ctx, ty_hint)

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
                t_ctx.types[generic.name] = Scheme([], ty_generic)
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

                ctx.types["$" + variant.id] = Scheme.from_subst(subst, ctx, ty_variant_con)
                ctx.types[variant.id] = Scheme.from_subst(
                    subst, ctx, typed.TDef(ty_variant, ty)
                )

            ctx.types[id] = Scheme.from_subst(subst, ctx, ty_con)

            return subst, typed.TUnit
        case terms.EUnaryExpr(op, expr):
            match op:
                case "-" | "+":
                    subst, ty_expr = infer(subst, ctx, expr)
                    subst = unify_subst(ty_expr, typed.TNum, subst)
                    return subst, typed.TNum
                case "!":
                    subst, _ = infer(subst, ctx, expr)
                    return subst, typed.TBool
                case "not":
                    subst, ty_expr = infer(subst, ctx, expr)
                    subst = unify_subst(ty_expr, typed.TBool, subst)
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
            ctx.vars[id] = Scheme([], ty)
            return subst, ty
        case terms.EParam(id, hint):
            subst, ty = infer(subst, ctx, hint)
            ctx.vars[id] = Scheme([], ty)
            return subst, ty
        case terms.EVariantCall(id, args):
            # option_con = TCon('Option', KFun(KStar(),KStar()))
            # ty = TAp<option_con, var1>
            # ty_variant_con = TCon('Some', KFun(KStar(),KStar()))
            # ty_variant = TAp<ty_var_con, var1>
            # ty_con = ty_variant -> ty
            ty = fresh_ty_var()
            subst, ty_con = infer(subst, ctx, terms.ETypeIdentifier(id))

            ty_args = list[typed.Type]()

            for arg in args:
                subst, ty_arg = infer(subst, ctx, arg)
                ty_args.append(ty_arg)

            kind_variant = functools.reduce(
                flip(typed.KFun), map(typed.kind, ty_args), typed.KStar().w()
            )

            subst, ty_variant_con = infer(subst, ctx, terms.ETypeIdentifier("$" + id))

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

        case terms.MaybeOrElse(value) | terms.MaybeEHint(value) | terms.EExpr(value):
            return infer(subst, ctx, value)
        case terms.EBinaryOpDef(id, params, body, hint, generics) | terms.EDef(
            id, params, body, hint, generics
        ):
            t_ctx = ctx.copy()

            for generic in generics:
                ty_generic = fresh_ty_var()
                t_ctx.types[generic.name] = Scheme([], ty_generic)

            subst, ty_hint = infer(subst, t_ctx, hint)

            ty_params = list[typed.Type]()

            for param in reversed(params):
                subst, ty_param = infer(subst, t_ctx, param)
                ty_params.append(ty_param)

            ty = reduce_args(ty_params, ty_hint)

            #
            subst, ty_body = infer(subst, t_ctx, body)

            subst = unify_subst(ty_body, ty_hint, subst)

            ctx.vars[id] = Scheme.from_subst(subst, ctx, ty)

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
        case terms.MaybeOrElseNothing():
            return subst, typed.TUnit
        case terms.MaybeEHintNothing():
            return subst, fresh_ty_var()

        case terms.EHint(id, args):
            subst, ty_con = infer(subst, ctx, terms.ETypeIdentifier(id))

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
            ctx.vars["$"] = Scheme.from_subst(subst, ctx, ty_expr)

            tree = case_tree.gen_match(cases)

            subst, ty = infer_case_tree(subst, ctx, tree)

            return subst, ty

        case terms.EArray(args):
            ty = fresh_ty_var()
            for arg in args:
                subst, ty1 = infer(subst, ctx, arg)
                subst = unify_subst(ty1, ty, subst)

            return subst, typed.TArray(ty)
        case node:
            typed.assert_never(node)


def type_infer(ctx: Context, node: Inferable) -> typed.Type:
    s, t = infer({}, ctx, node)
    return apply_subst(s, t)


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
    subst: Substitution,
    ctx: Context,
    tree: case_tree.CaseTree,
    o_alts: dict[str, list[str]] | None = None,
) -> tuple[Substitution, typed.Type]:
    alts = o_alts or {}

    match tree:
        case case_tree.MissingLeaf():
            if any(alts.values()):
                raise NonExhaustiveMatchException()
            return subst, fresh_ty_var()
        case case_tree.Node(var, pattern_name, vars, yes, no):

            subst, ty_var = infer(subst, ctx, terms.EIdentifier(var))  # x | x.0
            subst, ty_pattern_name = infer(
                subst, ctx, terms.ETypeIdentifier(pattern_name)
            )  # Some() | None()
            t_ctx = ctx.copy()

            # exhaustive
            if var not in alts:
                alts[var] = alternatives(ty_pattern_name)

            if pattern_name in alts[var]:
                alts[var].remove(pattern_name)

            ty_vars = list[typed.Type](fresh_ty_var() for _ in vars)

            subst, pattern_name_con = infer(
                subst, ctx, terms.ETypeIdentifier("$" + pattern_name)
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
                t_ctx.vars[var2] = Scheme.from_subst(subst, t_ctx, ty_var)

            # subst return type
            ty = fresh_ty_var()

            subst, ty_yes = infer_case_tree(
                subst,
                t_ctx,
                yes,
                {key: value for key, value in alts.items() if key != var}
                | {var2: alternatives(t_ctx.vars[var2].ty) for var2 in vars},
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
