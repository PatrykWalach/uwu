from typed import Type, TNum, TStr
from functools import partial
from typing import TypeAlias, overload
from typed_terms import *
from terms import *
Constraint: TypeAlias = tuple[Type, Type]


@overload
def collect(typed_node: list[TypedAstTree]) -> set[Constraint]:
    ...


@overload
def collect(typed_node: TypedAstTree) -> set[Constraint]:
    ...


def collect(typed_node: TypedAstTree | list[TypedAstTree]) -> set[Constraint]:
    match typed_node:
        case [*nodes]:
            return set.union(*map(collect, nodes), set())
        case Typed():
            pass
        case _:
            raise TypeError(f"{typed_node=}")

    ty = typed_node.ty
    match typed_node.node:
        case EVariableDeclaration(Typed(id_type, EIdentifier()), init):
            return collect(init) | {(id_type, init.ty), (ty, id_type)}
        case EDo(body):
            return collect(body) | {(ty, body[-1].ty)}
        case EProgram(body):
            return collect(body) | {(ty, body[-1].ty)}
        case EIdentifier():
            return set()
        case ELiteral(_, str()):
            return {(ty, TStr())}
        case ELiteral(_, float()):
            return {(ty, TNum())}
        case EBinaryExpr('++', left, right):
            return collect(left) | collect(right) | {(ty, TStr()), (left.ty, TStr()), (right.ty, TStr())}
        case EBinaryExpr('+' | '-' | '/' | '*' | '//', left, right):
            return collect(left) | collect(right) | {(ty, TNum()), (left.ty, TNum()), (right.ty, TNum())}
        case  EDef(id, params, body, hint):

            return collect(id) | collect(params) | collect(body) | {(ty, typed.TGeneric('Def', (
                typed.TGeneric('Params',
                               tuple(param.ty for param in params)),
                body.ty
            )
            )), (ty, id.ty)} | collect_hint(body.ty, hint)
        case  EParam(id, hint):
            return collect(id) | {(ty, id.ty), } | collect_hint(ty, hint)
        case ECall(callee, args):
            return collect(callee) | collect(args) |  {
                (callee.ty, typed.TGeneric('Def', (
                    typed.TGeneric('Params',       tuple(
                        arg.ty for arg in args)),     ty
                )))
                }
        case _:
            raise TypeError(f"{typed_node.node=}")


def collect_hint(ty, hint):
    if hint == None:
        return set()
    else:
        return {(ty, hint)}
