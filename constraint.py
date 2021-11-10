from typed import Type, number, string
from functools import partial
from typing import TypeAlias, overload
from typed_terms import *
from terms import *
Constraint: TypeAlias = tuple[Type,Type]


@overload
def collect(typed_node: list[TypedAstTree])->set[Constraint]:
    ...

@overload
def collect(typed_node: TypedAstTree)->set[Constraint]:
    ...

def collect(typed_node: TypedAstTree|list[TypedAstTree])->set[Constraint]:
    match typed_node:
        case [*nodes]:
            return set.union(*map(collect, nodes),set())
        case Typed():
            pass
        case _:
            raise TypeError(f"{typed_node=}")

    ty = typed_node.ty
    match typed_node.node:
        case VariableDeclaration(Typed(id_type,Identifier()),init):
            return collect(init) | {(id_type,init.ty),(ty,id_type)}
        case Do(body): 
            return collect(body) | {(ty,body[-1].ty)}
        case Program(body):
            return collect(body) | {(ty,body[-1].ty)}
        case Identifier():
            return set()
        case Literal(_, str()):
            return {(ty, string())}
        case Literal(_, float()):
            return {(ty, number())}
        case BinaryExpr('++', left,right):
            return    collect(left) |  collect(right) |  {(ty, string()),(left.ty, string()),(right.ty, string())}
        case BinaryExpr('+'|'-'|'/'|'*'|'//', left,right):
            return    collect(left) |  collect(right) |  {(ty, number()),(left.ty, number()),(right.ty, number())}
        case  Def(id, params,body,hint):

            return  collect(id) | collect(params) | collect(body) | {(ty,typed.GenericType('Def', (
                typed.GenericType('Params',
                tuple(param.ty for param in params)),
                body.ty
            )
            )),(ty,id.ty)} |collect_hint(body.ty,hint)
        case  Param(id, hint):
            return collect(id) | {(ty,id.ty),} | collect_hint(ty, hint)
        case Call(callee, args):
            return collect(callee) | collect(args) | {
            (callee.ty, typed.GenericType('Def', (
                typed.GenericType('Params',
                tuple(arg.ty for arg in args)),
                ty
            ))
            )}
        case _:
            raise TypeError(f"{typed_node.node=}")


def collect_hint(ty,hint):
    if hint == None:
        return set()
    else:
        return {(ty,hint)}