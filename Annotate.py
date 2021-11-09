
from typing import overload
import typed

from  typed_terms import * 
from  terms import * 

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


 

    @overload
    def __call__(self,node:AstTree) -> TypedAstTree:
        ...

    @overload
    def __call__(self,node:list[AstTree]) -> list[TypedAstTree]:
        ...

    def __call__(self,node:AstTree|list[AstTree]) -> TypedAstTree|list[TypedAstTree]:
        match node:
            case [*nodes]:
                return list(map(self,nodes))
            case VariableDeclaration(Identifier(id), init):
                id_type = self.fresh_var()
                self.env.set(id, id_type)
                typed_id = TypedIdentifier(id,id_type)
                return TypedVariableDeclaration(typed_id, self(init),self.fresh_var())
            case TypedVariableDeclaration(Identifier(id), init, type):
                id_type = self.fresh_var()
                self.env.set(id, id_type)
                typed_id = TypedIdentifier(id,id_type)
                return TypedVariableDeclaration(typed_id, self(init),type)
            case Literal(raw,  value):
                return TypedLiteral(raw,value,self.fresh_var())
            case Program(body):
                return TypedProgram(self(body),self.fresh_var())
            case TypedDo(body, type):
                self.env.append()
                body = self(body)
                self.env.pop()
                return TypedDo(body,type)
            case Do(body):
                self.env.append()
                body = self(body)
                self.env.pop()
                return TypedDo(body,self.fresh_var())
            case Identifier(name):
                return TypedIdentifier(name,self.env.get(name))
            case BinaryExpr(op, left,right):
                return TypedBinaryExpr(op, self(left),self(right),self.fresh_var())
            case _:
                raise TypeError(f"{node=}")


class VisitorTypeException(Exception):
    pass