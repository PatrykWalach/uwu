from __future__ import annotations
import operator
import functools
from typing import Callable, overload
import typed

from typed_terms import *
from terms import *
from util import ap

T = typing.TypeVar('T')
S = typing.TypeVar('S')
K = typing.TypeVar('K')


class Env(typing.Generic[T, S]):
    def __init__(self, *envs: dict[T, S]) -> None:
        self.envs = list(envs)

    def pop(self):
        self.envs.pop()

    def append(self):
        self.envs.append({})

    def get(self, attr: T) -> S:
        for env in self.envs:
            if attr in env:
                return env[attr]
        raise AttributeError

    def set(self, attr: T, value: S) -> None:
        self.envs[-1][attr] = value

    # def values(self):
    #     return functools.reduce(operator.or_, self.envs, {}).values()

    def map_values(self, fn: Callable[[S], K]) -> Env[T, K]:
        envs = (dict(zip(env.keys(), map(fn, env.values()))) for env in self.envs)
            
        return Env(*envs)

    # def items(self):
    #     return functools.reduce(operator.or_, self.envs, {}).items()

    # def keys(self):
    #     return functools.reduce(operator.or_, self.envs, {}).keys()


class Annotate:
    def __init__(self, env: dict[str, typed.Type]) -> None:
        self.counter = 0
        self.env = Env(env)

    counter = 0

    def fresh_var(self):
        global counter
        self.counter += 1
        return typed.TVar(self.counter)

    def __call__(self, node: AstTree) -> TypedAstTree:
        print(f"{node=}")
        match node:
            case EVariableDeclaration(EIdentifier(id), init):
                id_type = self.fresh_var()
                self.env.set(id, id_type)
                typed_id = Typed(id_type, EIdentifier(id))
                return Typed(self.fresh_var(), EVariableDeclaration(typed_id, self(init)))
            case ELiteral(raw,  value):
                return Typed(self.fresh_var(), ELiteral(raw, value))
            case EProgram(body):
                return Typed(self.fresh_var(), EProgram(ap(self, body)))
            case EDo(body):
                self.env.append()
                body = ap(self, body)
                self.env.pop()
                return Typed(self.fresh_var(), EDo(body))
            case EIdentifier(name):
                return Typed(self.env.get(name), EIdentifier(name))
            case EBinaryExpr(op, left, right):
                return Typed(self.fresh_var(), EBinaryExpr(op, self(left), self(right)))
            case EParam(EIdentifier(id), hint):
                id_type = self.fresh_var()
                self.env.set(id, id_type)
                typed_id = Typed(id_type, EIdentifier(id))
                return Typed(self.fresh_var(), EParam(typed_id, hint))
            case EDef(EIdentifier(id), params, body, hint):
                id_type = self.fresh_var()
                self.env.set(id, id_type)
                typed_id = Typed(id_type, EIdentifier(id))
                self.env.append()
                params = ap(self, params)
                body = self(body)
                self.env.pop()
                return Typed(self.fresh_var(), EDef(
                    typed_id,
                    params,
                    body,
                    hint
                ))
            case ECall(id, args):
                typed_id = self(id)
                return Typed(self.fresh_var(), ECall(typed_id, ap(self, args)))
            case _:
                raise TypeError(f"{node=}")


class VisitorTypeException(Exception):
    pass
