from __future__ import annotations

import terms
import typed


def to_string(exp: terms.AstNode) -> str:
    match exp:
        case terms.EMaybeOrElse(value):
            return to_string(value)
        case terms.EExternal(value=value):
            return f"`{value}`"
        case terms.EStrLiteral(value):
            return f"'{exp.value}'"
        case terms.ENumLiteral(value) | terms.EFloatLiteral(value):
            return f"{exp.value}"
        case terms.ELet(id, init):
            return f"{id} = {to_string(init)}"
        case terms.EBlock(body):
            return "\n".join(map(to_string, body))
        case terms.EDo(block):
            return "do\n" + to_string(block).replace("\n", "  \n") + "\nend"
        case terms.EProgram(body):

            return "\n".join(map(to_string, body))
        case terms.EMaybeOrElseNothing():
            return f""
        case terms.EIf(test, then, or_else):
            return f"if {to_string(test)} then {to_string(then)} {to_string(or_else)}"
        case terms.ECall(id, args):
            str_args = ",".join(map(to_string, args))
            return f"{to_string(id)}({str_args})"

        case terms.EVariantCall(id, args):
            str_args = ",".join(map(to_string, args))
            return f"{id}({str_args})"

        case terms.EDef(id, args, do):
            str_args = ",".join(map(to_string, args))
            return f"def {id}({str_args}) {to_string(do)}"

        case terms.EBinaryExpr(op, left, right):
            return f"{to_string(left)}{op}{to_string(right)}"
        case terms.EIdentifier(id):
            return id
        case terms.EEnumDeclaration():
            return ""
        case terms.EParam(id):
            return id
        case terms.EExpr(value):
            return to_string(value)

        case exp:
            typed.assert_never(exp)
