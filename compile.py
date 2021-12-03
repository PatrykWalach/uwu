
from algorithm_j import Context
import terms


def compile(ctx: Context, exp: terms.AstTree) -> str:
    match exp:
        case terms.ELiteral(value=str() as value):
            return f'"{value}"'
        case terms.ELiteral(value=float() as value):
            return f"{value}"
        case terms.EVariableDeclaration(terms.EIdentifier(id), init):
            return f"{id}={compile(ctx, init)};"
        case terms.EDo(body):
            body = [compile(ctx, expr) for expr in body]
            body[-1] = 'return ' + body[-1]
            return "(()=>{"+"".join(body)+"})()"
        case _:
            return NotImplemented
