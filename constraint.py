from typed import Type, number, string
from functools import partial
from typing import TypeAlias
from typed_terms import *

Constraint: TypeAlias = tuple[Type,Type]

def collect(typed_node: TypedAstTree)->set[Constraint]:
    match typed_node:
        case TypedVariableDeclaration(TypedIdentifier(type=id_type),init,type):
            return collect(init) | {(id_type,init.type),(type,id_type)}
        case TypedDo(body,type): 
            return set.union(*map(partial(collect),body)
            ) | {(type,body[-1].type)}
        case TypedProgram(body,type):
            return set.union(*map(partial(collect),body)) | {(type,body[-1].type)}
        case TypedIdentifier():
            return set()
        case TypedLiteral(_, str(), type):
            return {(type, string())}
        case TypedLiteral(_, float(), type):
            return {(type, number())}
        case TypedBinaryExpr('++', left,right,type):
            return    collect(left) |  collect(right) |  {(type, string()),(left.type, string()),(right.type, string())}
        case TypedBinaryExpr('+'|'-'|'/'|'*'|'//', left,right,type):
            return    collect(left) |  collect(right) |  {(type, number()),(left.type, number()),(right.type, number())}
        case _:
            raise TypeError(f"{typed_node=}")