from __future__ import annotations

import dataclasses
import functools
import itertools
from dataclasses import dataclass

import case_tree
import terms
import typed


class Hoist(terms.FoldAll):
    def __init__(self) -> None:
        super().__init__()
        self.to_hoist = list[terms.EExpr]()

    def EExpr(self, n: terms.EExpr) -> terms.EExpr:

        n = n.fold_children_with(self)
        match n.expr:
            case terms.ELet(id) | terms.EDef(id):
                self.to_hoist.append(n)
                return terms.EExpr(terms.EIdentifier(id))

        return n

    def EProgram(self, n: terms.EProgram) -> terms.EProgram:

        body2 = self.hoist_expr_list(n.body)
        return terms.EProgram(filter_identifiers(body2))

    def hoist_expr_list(self, body: list[terms.EExpr]) -> list[terms.EExpr]:
        body2 = list[terms.EExpr]()

        for expr in body:
            hoist = Hoist()
            expr2 = expr.fold_with(hoist)
            body2.extend(hoist.to_hoist)
            body2.append(expr2)

        return body2

    def EBlock(self, n: terms.EBlock) -> terms.EBlock:
        body2 = self.hoist_expr_list(n.body)
        return terms.EBlock(filter_identifiers(body2[:-1:]) + body2[-1::])


def filter_identifiers(body: list[terms.EExpr]) -> list[terms.EExpr]:
    return list(filter(lambda expr: not isinstance(expr.expr, terms.EIdentifier), body))


# def compile(program: terms.EProgram):
#     ast = program.fold_with(Hoist())
#     return _compile(ast)


def compile(
    exp: terms.EIdentifier
    | terms.EExpr
    | terms.EProgram
    | terms.EParam
    | terms.EUnaryExpr
    | terms.MaybeOrElse
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
    | terms.EIf
    | terms.ENumLiteral
    | terms.EStrLiteral
    | terms.EFloatLiteral
    | terms.MaybeOrElseNothing,
) -> str:
    match exp:
        case terms.MaybeOrElse(value):
            return compile(value)
        case terms.EExternal(value=value):
            return f"{value}"
        case terms.EStrLiteral(value):
            return f'"{exp.value}"'
        case terms.ENumLiteral(value) | terms.EFloatLiteral(value):
            return f"{exp.value}"
        case terms.ELet(id, init):
            return f"const {id}={compile( init)}"
        case terms.EBlock(body):
            js_body = [compile(expr) for expr in body]
            if js_body:
                js_body[-1] = "return " + js_body[-1]
            return ";".join(js_body)
        case terms.EDo(block):
            return "(()=>{" + compile(block) + "})()"
        case terms.EProgram(body):
            js_body = [compile(expr) for expr in body]
            return ";".join(js_body)
        case terms.MaybeOrElseNothing():
            return f"return"
        case terms.EIf(test, then, or_else):
            return (
                f"(()=>{{if({compile(test)}){{{compile(then)}}}{compile(or_else)}}})()"
            )
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

        case terms.EVariantCall(id, args):
            js_var_args = [f"_{i}:{compile(arg)}" for i, arg in enumerate(args)]

            return f"{{TAG:'{id}',{','.join(js_var_args)}}}"

        case terms.EDef(id, args, terms.EDo(block)):

            js_args = functools.reduce(
                lambda acc, js_arg: f"{acc}({js_arg})=>",
                [compile(arg) for arg in args] or [""],
                "",
            )

            return f"const {id}={js_args}{{{compile(block)}}}"
        case terms.EBinaryExpr(op, left, right):
            js_left = compile(left)
            js_right = compile(right)
            match op:
                case "|":
                    return f"{js_left}.concat({js_right})"
                case "++":
                    return f"({js_left}+{js_right})"
                case "/":
                    return f"Math.floor({js_left}/{js_right})"
                case "!=" | "==":
                    return f"({js_left}{op}={js_right})"
                case ">" | "<" | "+" | "-" | "/" | "*":
                    return f"({js_left}{op}{js_right})"
                case "+." | "-." | "/." | "*.":
                    return f"({js_left}{op[:-1:]}{js_right})"
                case op:
                    typed.assert_never(op)

        case terms.EIdentifier(id):
            return id
        case terms.EEnumDeclaration():
            return ""
        case terms.EParam(id):
            return id
        case terms.ECaseOf(expr, cases):
            return f"(()=>{{const $={compile(expr)};{_compile_case_tree(case_tree.gen_match(cases))}}})()"
            # cases = [f"{_compile(case)}" for case in cases]
            # cases = [*cases, "throw new Error('Unhandled case of')"]

            # return f"((__)=>{{{';'.join(cases)}}})({_compile(of)})"
        # case terms.ECase(pattern, body):
        #     return f"if({_compile(pattern)}(__)){{return {_compile(body)}}}"
        # case terms.EMatchAs(id):
        #     return f"((__)=>{{{id}=__; return true}})"
        # case terms.EMatchVariant("True", []):
        #     return f"((__)=>{{return __===true}})"
        # case terms.EMatchVariant("False", []):
        #     return f"((__)=>{{return __===false}})"
        # case terms.EMatchVariant(id, []):
        #     return f"((__)=>{{return __==='{id}'}})"
        # case terms.EMatchVariant(id, fields) if fields:
        #     fields = [f"{compile(field)}(__._{i})" for i, field in enumerate(fields)]
        #     fields = [f'__.TAG==="{id}"', *fields]
        #     fields = "&&".join(fields)

        #     return f"((__)=>{{return {fields}}})"
        case terms.EExpr(value):
            return compile(value)
        case terms.EArray(args):
            return f"[{','.join(map(compile, args))}]"
        case terms.EUnaryExpr(op, expr):
            return f"{op}({compile(expr)})"
        case exp:
            typed.assert_never(exp)


def _compile_case_tree(tree: case_tree.CaseTree) -> str:
    match tree:
        case case_tree.Leaf(body):
            return compile(body.block)
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
            typed.assert_never(tree)
