
from typing import overload
import typed

from  typed_terms import * 
from  terms import *
from util import ap 

class Env:
    def __init__(self,env:dict[str,typed.Type]) -> None:
        self.envs =[env]
    
    def pop(self):
        self.envs.pop()

    def append(self):
        self.envs.append({})

    def get(self, attr: str) -> typed.Type:
        for env in self.envs:
            if attr in env:
                return env[attr]
        raise AttributeError
    
    def set(self, attr: str, value: typed.Type) -> None:
        self.envs[-1][attr]=value


class Annotate():
    def __init__(self,env:dict[str,typed.Type]) -> None:
        self.counter = 0
        self.env =Env(env)

    counter=0
    def fresh_var(self):
        global counter
        self.counter+=1
        return typed.Var(self.counter)


 

    def __call__(self,node:AstTree) -> TypedAstTree:
        print(f"{node=}")
        match node:
            case VariableDeclaration(Identifier(id), init):
                id_type = self.fresh_var()
                self.env.set(id, id_type)
                typed_id = Typed(id_type,Identifier(id))
                return Typed(self.fresh_var(),VariableDeclaration(typed_id, self(init)))
            case Literal(raw,  value):
                return Typed(self.fresh_var(),Literal(raw,value))
            case Program(body):
                return Typed(self.fresh_var(),Program(ap(self,body)))
            case Do(body):
                self.env.append()
                body = ap(self,body)
                self.env.pop()
                return Typed(self.fresh_var(),Do(body))
            case Identifier(name):
                return Typed(self.env.get(name),Identifier(name))
            case BinaryExpr(op, left,right):
                return Typed(self.fresh_var(),BinaryExpr(op, self(left),self(right)))
            case Param(Identifier(id), hint):
                id_type = self.fresh_var()
                self.env.set(id, id_type)
                typed_id = Typed(id_type,Identifier(id))
                return Typed(self.fresh_var(),Param(typed_id,hint))
            case Def(Identifier(id),params,body,hint):
                id_type = self.fresh_var()
                self.env.set(id, id_type)
                typed_id = Typed(id_type,Identifier(id))
                self.env.append()
                params = ap(self,params)
                body = self(body)
                self.env.pop()
                return Typed(self.fresh_var(),Def(
                    typed_id,
                    params,
                    body,
                    hint
                ))
            case Call(id, args):
                typed_id= self(id)
                return Typed(self.fresh_var(),Call(typed_id,ap(self,args)))
            case _:
                raise TypeError(f"{node=}")


class VisitorTypeException(Exception):
    pass