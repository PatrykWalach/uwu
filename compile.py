import enum
from attr.validators import instance_of
from algorithm_j import Context
import terms
import functools


def compile(exp: terms.AstTree) -> str:

    match exp:
        case terms.ELiteral(value=str()):
            return f'"{exp.value}"'
        case terms.ELiteral(value=float()):
            return f"{exp.value}"
        case terms.EVariableDeclaration(terms.EIdentifier(id), init):
            return f"{id}={compile( init)}"
        case terms.EBlockStmt(body):
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
            return "(()=>{" + ";".join(body) + "})()"
        case terms.EIf(test, then, or_else=None):
            return f"(()=>{{if({compile(test)}.TAG==='True'){{{compile(then)}}}else{{{{TAG:'None'}}}}}})()"
        case terms.EIf(test, then, or_else) if or_else != None:
            return f"(()=>{{if({compile(test)}.TAG==='True'){{{compile(then)}}}else{{{compile(or_else)}}}}})()"
        case terms.EIdentifier("print"):
            return f"console.log"
        case terms.EIdentifier("unit"):
            return f"undefined"
        case terms.ECall((id), args):
            return functools.reduce(
                lambda acc, arg: f"{acc}({arg})",
                [compile(arg) for arg in args] or [""],
                compile(id),
            )

        case terms.EDef(terms.EIdentifier(id), args, body):

            args = functools.reduce(
                lambda acc, arg: f"{acc}({arg})=>",
                [compile(arg) for arg in args] or [""],
                "",
            )

            return f"{id}={args}{compile(body)}"
        case terms.EBinaryExpr("++", left, right):
            return f"({compile( left)}+{compile( right)})"
        case terms.EBinaryExpr("//", left, right):
            return f"Math.floor({compile( left)}/{compile( right)})"
        case terms.EBinaryExpr(">" | "<" | "<=" | ">=" as op, left, right):
            return f"({compile( left)}{op}{compile( right)}?{{TAG:'True'}}:{{TAG:'False'}})"
        case terms.EBinaryExpr("+" | "-" | "/" | "*" as op, left, right):
            return f"({compile( left)}{op}{compile( right)})"
        case terms.EIdentifier(id):
            return id
        case terms.EEnumDeclaration(terms.EIdentifier(id), generics, variants):
            str_variants = list[str]()

            for var in variants:
                fields = [
                    f"_{i}: {field.name}" for i, field in enumerate(var.fields.unnamed)
                ]

                body = functools.reduce(
                    lambda acc, arg: f"({arg})=>{acc}",
                    ([field.name for field in reversed(var.fields.unnamed)]) or [""],
                    f"({{TAG:'{var.id.name}',{','.join(fields)}}})",
                )

                str_variant = f"{var.id.name}={  body  }"

                str_variants.append(str_variant)

            return ";".join(str_variants)
        case terms.EParam(terms.EIdentifier(id)):
            return id
        case terms.ECaseOf(of, cases):
            cases = [f"{compile(case)}" for case in cases]

            return f"((__)=>{{{';'.join(cases)}}})({compile(of)})"
        case terms.ECase(pattern, body):
            return f"if({compile(pattern)}(__)){{return {compile(body)}}}"
        case terms.EMatchAs(terms.EIdentifier(id)):
            return f"((__)=>{{{id}=__; return true}})"
        case terms.EEnumPattern(terms.EIdentifier(id), fields):
            fields = [f"{compile(field)}(__._{i})" for i, field in enumerate(fields)]
            fields = [f'__.TAG==="{id}"', *fields]
            fields = "&&".join(fields)

            return f"((__)=>{{return {fields}}})"
        case terms.EArray(args) | terms.ETuple(args):
            return f"[{','.join(map(compile, args))}]"
        case terms.EMatchTuple(patterns)|terms.EMatchArray(patterns):

            patterns = [f"{compile(pattern)}(__[{i}])" for i, pattern in enumerate(patterns)]
            patterns = [
                f"__.length=={len(patterns)}",
                *patterns,
            ]

            patterns = "&&".join(patterns)

            return f"((__)=>{{return {patterns}}})"
        case _:
            raise Exception(f"Unsupported expression: {exp}")