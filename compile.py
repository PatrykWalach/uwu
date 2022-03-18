from __future__ import annotations

import functools

import case_tree
import terms


def compile(exp: terms.AstTree) -> str:

    match exp:
        case terms.EExternal(value=value):
            return f"{value}"
        case terms.ELiteral(value=str()):
            return f'"{exp.value}"'
        case terms.ELiteral(value=float()):
            return f"{exp.value}"
        case terms.ELet(id, init):
            return f"const {id}={compile( init)}"
        case terms.EBlock(body):
            body = [compile(expr) for expr in body]
            if body:
                body[-1] = "return " + body[-1]
            return ";".join(body)
        case terms.EDo(body):
            body = [compile(expr) for expr in body]
            if body:
                body[-1] = "return " + body[-1]
            return "(()=>{" + ";".join(body) + "})()"
        case terms.EProgram(body):
            body = [compile(expr) for expr in body]
            return ";".join(body)
        case terms.EIfNone():
            return f"return"
        case terms.EIf(test, then, or_else):
            return f"(()=>{{if({compile(test)}){{{compile(then)}}}else{{{compile(or_else)}}}}})()"
        case terms.ECall(id, args):
            return functools.reduce(
                lambda acc, arg: f"{acc}({arg})",
                [compile(arg) for arg in args] or [""],
                compile(id),
            )

        case terms.EVariantCall("True", []):
            return f"true"
        case terms.EVariantCall("False", []):
            return f"false"

        case terms.EVariantCall(id, []):
            return f"'{id}'"

        case terms.EVariantCall(id, args) if args:
            args = [f"_{i}:{compile(arg)}" for i, arg in enumerate(args)]

            return f"{{TAG:'{id}',{','.join(args)}}}"

        case terms.EDef(id, args, body):

            args = functools.reduce(
                lambda acc, arg: f"{acc}({arg})=>",
                [compile(arg) for arg in args] or [""],
                "",
            )

            return f"const {id}={args}{compile(body)}"
        case terms.EBinaryExpr("|", left, right):
            return f"{compile( left)}.concat({compile( right)})"
        case terms.EBinaryExpr("++", left, right):
            return f"({compile( left)}+{compile( right)})"
        case terms.EBinaryExpr("//", left, right):
            return f"Math.floor({compile( left)}/{compile( right)})"
        case terms.EBinaryExpr("!=" | "==" as op, left, right):
            return f"({compile( left)}{op}={compile( right)})"
        case terms.EBinaryExpr(
            ">" | "<" | "+" | "-" | "/" | "*" | "%" as op, left, right
        ):
            return f"({compile( left)}{op}{compile( right)})"
        case terms.EIdentifier(id):
            return id
        case terms.EEnumDeclaration():
            return ""
        case terms.EParam(id):
            return id
        case terms.ECaseOf(expr, cases):
            return f"(()=>{{const $={compile(expr)};{compile_case_tree(case_tree.gen_match(cases))}}})()"
            # cases = [f"{compile(case)}" for case in cases]
            # cases = [*cases, "throw new Error('Unhandled case of')"]

            # return f"((__)=>{{{';'.join(cases)}}})({compile(of)})"
        # case terms.ECase(pattern, body):
        #     return f"if({compile(pattern)}(__)){{return {compile(body)}}}"
        case terms.EMatchAs(id):
            return f"((__)=>{{{id}=__; return true}})"
        case terms.EMatchVariant("True", []):
            return f"((__)=>{{return __===true}})"
        case terms.EMatchVariant("False", []):
            return f"((__)=>{{return __===false}})"
        case terms.EMatchVariant(id, []):
            return f"((__)=>{{return __==='{id}'}})"
        case terms.EMatchVariant(id, fields) if fields:
            fields = [f"{compile(field)}(__._{i})" for i, field in enumerate(fields)]
            fields = [f'__.TAG==="{id}"', *fields]
            fields = "&&".join(fields)

            return f"((__)=>{{return {fields}}})"
        case terms.EArray(args) | terms.ETuple(args):
            return f"[{','.join(map(compile, args))}]"
        case terms.EUnaryExpr(op, expr):
            return f"{op}({compile(expr)})"
        case terms.EMatchTuple(patterns) | terms.EMatchArray(patterns):

            patterns = [
                f"{compile(pattern)}(__[{i}])" for i, pattern in enumerate(patterns)
            ]
            patterns = [
                f"__.length=={len(patterns)}",
                *patterns,
            ]

            patterns = "&&".join(patterns)

            return f"((__)=>{{return {patterns}}})"
        case _:
            raise Exception(f"Unsupported expression: {exp}")


def compile_case_tree(tree: case_tree.CaseTree):
    match tree:
        case case_tree.Leaf(body):
            return compile(terms.EBlock(body.body))
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
            #     return compile_case_tree(yes)

            return f"if({'&&'.join(conditions)}){{{compile_case_tree(yes)}}}{compile_case_tree(no)}"
        case _:
            raise TypeError("Unsupported case")
