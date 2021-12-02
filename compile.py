
from algorithm_j import Context
import terms


def compile(ctx: Context, exp: terms.AstTree) -> str:
    match exp:
        case terms.ELiteral(value=str() as value):
            return f'"{value}"'
        case terms.ELiteral(value=float() as value):
            return f"{value}"
        case _:
            return NotImplemented
