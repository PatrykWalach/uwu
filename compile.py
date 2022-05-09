from __future__ import annotations

import dataclasses
import functools
import itertools
from dataclasses import dataclass

import case_tree
import terms
import typed


def hoist_expr_list(body: list[terms.Expr]) -> list[terms.Expr]:
    body2 = list[terms.Expr]()

    for expr in body:
        let, expr2 = hoist_expr(expr)
        body2.extend(let)
        body2.append(expr2)

    return body2


def filter_identifiers(body: list[terms.Expr]):
    return list(filter(lambda expr: not isinstance(expr, terms.EIdentifier), body))


def hoist_do(
    node: terms.EDo,
) -> terms.EDo:
    body2 = hoist_expr_list(node.body)

    return terms.EDo(filter_identifiers(body2[:-1:]) + body2[-1::])


def hoist_case(
    node: terms.ECase,
) -> terms.ECase:

    return terms.ECase(
        node.pattern,
        body=hoist_do(node.body),
    )


def hoist(
    node: terms.EProgram | terms.EBlock,
) -> terms.EProgram | terms.EBlock:
    match node:
        case terms.EBlock(body):
            body2 = hoist_expr_list(body)
            return terms.EBlock(filter_identifiers(body2[:-1:]) + body2[-1::])

        case terms.EProgram(body):
            body2 = hoist_expr_list(body)
            return terms.EProgram(filter_identifiers(body2))

        case node:
            typed.assert_never(node)


def hoist_expr(node: terms.Expr) -> tuple[list[terms.Expr], terms.Expr]:
    match node:
        case terms.ELet(id, init):
            let, init2 = hoist_expr(init)

            return let + [dataclasses.replace(node, init=init2)], terms.EIdentifier(id)
        case terms.EDef(id, params, body, hint):

            return [
                terms.EDef(id, params, body=hoist_do(body), hint=hint)
            ], terms.EIdentifier(id)
        case terms.EIf(test, then, terms.EBlock() as or_else):
            let_test, test2 = hoist_expr(test)
            return let_test, dataclasses.replace(
                node,
                test=test2,
                then=hoist(then),
                or_else=hoist(or_else),
            )
        case terms.EIf(test, then, terms.EIf() | terms.EIfNone() as or_else):
            let_test, test2 = hoist_expr(test)
            let_or_else, or_else2 = hoist_expr(or_else)
            return let_test + let_or_else, dataclasses.replace(
                node,
                test=test2,
                then=hoist(then),
                or_else=or_else2,
            )

        case terms.ECall(callee, args):
            lets = list[terms.Expr]()
            args2 = list[terms.Expr]()
            for expr in args:
                let, expr2 = hoist_expr(expr)
                lets.extend(let)
                args2.append(expr2)

            return lets, terms.ECall(callee, args=args2)
        case terms.ECaseOf(expr, cases):
            let_expr, expr2 = hoist_expr(expr)
            return let_expr, terms.ECaseOf(expr2, list(map(hoist_case, cases)))

        case terms.EVariantCall(callee, args):
            lets = list[terms.Expr]()
            args2 = list[terms.Expr]()
            for expr in args:
                let, expr2 = hoist_expr(expr)
                lets.extend(let)
                args2.append(expr2)

            return lets, terms.EVariantCall(callee, args=args2)

        case terms.EArray(args):
            lets = list[terms.Expr]()
            args2 = list[terms.Expr]()
            for expr in args:
                let, expr2 = hoist_expr(expr)
                lets.extend(let)
                args2.append(expr2)

            return lets, terms.EArray(args=args2)

        case terms.EBinaryExpr(op, left, right):
            let_left, left2 = hoist_expr(left)
            let_right, right2 = hoist_expr(right)

            return let_left + let_right, terms.EBinaryExpr(op, left2, right2)
        case terms.EEnumDeclaration() | terms.EIdentifier() | terms.EExternal() | terms.ELiteral():
            return [], node
        case terms.EUnaryExpr(op, expr):
            let_expr, expr2 = hoist_expr(expr)
            return let_expr, terms.EUnaryExpr(op, expr2)
        case terms.EDo():
            return [], hoist_do(node)
        case node:
            typed.assert_never(node)


def compile(program: terms.EProgram):
    ast = hoist(program)
    return _compile(ast)


def _compile(exp: terms.AstTree) -> str:
    match exp:
        case terms.EExternal(value=value):
            return f"{value}"
        case terms.ELiteral(value=str()):
            return f'"{exp.value}"'
        case terms.ELiteral(value=float()):
            return f"{exp.value}"
        case terms.ELet(id, init):
            return f"const {id}={_compile( init)}"
        case terms.EBlock(body):
            body = [_compile(expr) for expr in body]
            if body:
                body[-1] = "return " + body[-1]
            return ";".join(body)
        case terms.EDo(body):
            body = [_compile(expr) for expr in body]
            if body:
                body[-1] = "return " + body[-1]
            return "(()=>{" + ";".join(body) + "})()"
        case terms.EProgram(body):
            body = [_compile(expr) for expr in body]
            return ";".join(body)
        case terms.EIfNone():
            return f"return"
        case terms.EIf(test, then, or_else):
            return f"(()=>{{if({_compile(test)}){{{_compile(then)}}}{_compile(or_else)}}})()"
        case terms.ECall(id, args):
            return functools.reduce(
                lambda acc, arg: f"{acc}({arg})",
                [_compile(arg) for arg in args] or [""],
                _compile(id),
            )

        case terms.EVariantCall("True", []):
            return f"true"
        case terms.EVariantCall("False", []):
            return f"false"

        case terms.EVariantCall(id, []):
            return f"'{id}'"

        case terms.EVariantCall(id, args) if args:
            args = [f"_{i}:{_compile(arg)}" for i, arg in enumerate(args)]

            return f"{{TAG:'{id}',{','.join(args)}}}"

        case terms.EDef(id, args, terms.EDo(body)):

            args = functools.reduce(
                lambda acc, arg: f"{acc}({arg})=>",
                [_compile(arg) for arg in args] or [""],
                "",
            )

            return f"const {id}={args}{{{_compile(terms.EBlock(body))}}}"
        case terms.EBinaryExpr("|", left, right):
            return f"{_compile( left)}.concat({_compile( right)})"
        case terms.EBinaryExpr("++", left, right):
            return f"({_compile( left)}+{_compile( right)})"
        case terms.EBinaryExpr("//", left, right):
            return f"Math.floor({_compile( left)}/{_compile( right)})"
        case terms.EBinaryExpr("!=" | "==" as op, left, right):
            return f"({_compile( left)}{op}={_compile( right)})"
        case terms.EBinaryExpr(
            ">" | "<" | "+" | "-" | "/" | "*" | "%" as op, left, right
        ):
            return f"({_compile( left)}{op}{_compile( right)})"
        case terms.EIdentifier(id):
            return id
        case terms.EEnumDeclaration():
            return ""
        case terms.EParam(id):
            return id
        case terms.ECaseOf(expr, cases):
            return f"(()=>{{const $={_compile(expr)};{_compile_case_tree(case_tree.gen_match(cases))}}})()"
            # cases = [f"{_compile(case)}" for case in cases]
            # cases = [*cases, "throw new Error('Unhandled case of')"]

            # return f"((__)=>{{{';'.join(cases)}}})({_compile(of)})"
        # case terms.ECase(pattern, body):
        #     return f"if({_compile(pattern)}(__)){{return {_compile(body)}}}"
        case terms.EMatchAs(id):
            return f"((__)=>{{{id}=__; return true}})"
        case terms.EMatchVariant("True", []):
            return f"((__)=>{{return __===true}})"
        case terms.EMatchVariant("False", []):
            return f"((__)=>{{return __===false}})"
        case terms.EMatchVariant(id, []):
            return f"((__)=>{{return __==='{id}'}})"
        case terms.EMatchVariant(id, fields) if fields:
            fields = [f"{_compile(field)}(__._{i})" for i, field in enumerate(fields)]
            fields = [f'__.TAG==="{id}"', *fields]
            fields = "&&".join(fields)

            return f"((__)=>{{return {fields}}})"
        case terms.EArray(args) | terms.ETuple(args):
            return f"[{','.join(map(_compile, args))}]"
        case terms.EUnaryExpr(op, expr):
            return f"{op}({_compile(expr)})"
        case terms.EMatchTuple(patterns) | terms.EMatchArray(patterns):

            patterns = [
                f"{_compile(pattern)}(__[{i}])" for i, pattern in enumerate(patterns)
            ]
            patterns = [
                f"__.length=={len(patterns)}",
                *patterns,
            ]

            patterns = "&&".join(patterns)

            return f"((__)=>{{return {patterns}}})"
        case _:
            raise Exception(f"Unsupported expression: {exp}")


def _compile_case_tree(tree: case_tree.CaseTree):
    match tree:
        case case_tree.Leaf(body):
            return _compile(terms.EBlock(body.body))
        case case_tree.MissingLeaf():
            return "throw new Error('Non-exhaustive pattern match')"
        case case_tree.Node(var, pattern_name, vars, yes, no):
            conditions = []

            if pattern_name == "True":
                conditions.append(f"{var}")
            if pattern_name == "False":
                conditions.append(f"!{var}")
            elif vars:
                conditions.insert(0, f"{var}.TAG==='{pattern_name}'")
                conditions.insert(0, f"typeof {var} !== 'string'")
            else:
                conditions.insert(0, f"{var}==='{pattern_name}'")

            # if isinstance(no, case_tree.MissingLeaf):
            #     return _compile_case_tree(yes)

            return f"if({'&&'.join(conditions)}){{{_compile_case_tree(yes)}}}{_compile_case_tree(no)}"
        case _:
            raise TypeError("Unsupported case")
