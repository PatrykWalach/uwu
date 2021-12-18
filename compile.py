
from algorithm_j import Context
import terms


def compile(exp: terms.AstTree) -> str:

    match exp:
        case terms.ELiteral(value=str() as value):
            return f'"{value}"'
        case terms.ELiteral(value=float() as value):
            return f"{value}"
        case terms.EVariableDeclaration(terms.EIdentifier(id), init):
            return f"{id}={compile( init)}"
        case terms.EBlockStmt(body):
            body = [compile(expr) for expr in body]
            body[-1] = 'return ' + body[-1]
            return ";".join(body)
        case terms.EDo(body):
            body = [compile(expr) for expr in body]
            body[-1] = 'return ' + body[-1]
            return "(()=>{"+";".join(body)+"})()"
        case terms.EProgram(body):
            body = [compile(expr) for expr in body]
            return "(()=>{"+";".join(body)+"})()"
        case terms.EIf(test, then, or_else=None):
            return f"(()=>{{if({compile(test)}._ == 'True'){{{compile(then)}}}else{{{{_:'None'}}}}}})()"
        case terms.EIf(test, then, or_else) if or_else != None:
            return f"(()=>{{if({compile(test)}._ == 'True'){{{compile(then)}}}else{{{compile(or_else)}}}}})()"
        case terms.ECall(terms.EIdentifier('print'), [arg]):
            return f"console.log({compile(arg)})"
        case terms.ECall(terms.EIdentifier(id), args):
            return f"{id}({','.join(map(compile, args))})"
        case terms.EDef(terms.EIdentifier(id), args, body):
            return f"{id}=({','.join(map(compile, args))})=>{{return {compile(body)}}}"
        case terms.EBinaryExpr('++', left, right):
            return f"({compile( left)}+{compile( right)})"
        case terms.EBinaryExpr('//', left, right):
            return f"Math.floor({compile( left)}/{compile( right)})"
        case terms.EBinaryExpr('>' | '<' | '<=' | '>=' as op, left, right):
            return f"({compile( left)}{op}{compile( right)}?{{_:'True'}}:{{_:'False'}})"
        case terms.EBinaryExpr('+' | '-' | '/' | '*' as op, left, right):
            return f"({compile( left)}{op}{compile( right)})"
        case terms.EIdentifier(id):
            return id
        case terms.EEnumDeclaration(terms.EIdentifier(id), generics, variants):
            str_variants = list[str]()

            for var in variants:
                fields = [f"_{i}: {field.name}" for i,
                          field in enumerate(var.fields.unnamed)]

                str_variant = f"{var.id.name}=({','.join([field.name for field in var.fields.unnamed ])})=>{{return {{_:'{var.id.name}',{','.join(fields)}}}}}"

                str_variants.append(str_variant)

            return ';'.join(str_variants)
        case terms.EParam(terms.EIdentifier(id)):
            return id
        case terms.ECaseOf(of, cases):
            cases = [f"{compile(case)}" for case in cases]

            return f"((__)=>{{{';'.join(cases)}}})({compile(of)})"
        case terms.ECase(pattern, body):
            return f"if({compile(pattern)}(__)){{return {compile(body)}}}"
        case terms.EParamPattern(terms.EIdentifier(id)):
            return f"((__)=>{{{id}=__; return true}})"
        case terms.EEnumPattern(terms.EIdentifier(id), fields):
            fields = [f"{compile(field)}(__._{i})" for i,
                      field in enumerate(fields)]
            fields = [f"__._ === \"{id}\"", *fields]
            fields = '&&'.join(fields)

            return f"((__)=>{{return {fields}}})"
        case _:
            raise Exception(f"Unsupported expression: {exp}")
