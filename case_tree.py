import dataclasses
import typing

import terms


def subst_var_eqs(case: terms.ECase):
    substitutions = {
        pattern.identifier: id
        for id, pattern in case.patterns.items()
        if isinstance(pattern, terms.EMatchAs)
    }

    patterns = {
        id: pattern
        for id, pattern in case.patterns.items()
        if not isinstance(pattern, terms.EMatchAs)
    }

    return patterns, dataclasses.replace(
        case.body,
        body=[]
        + [
            terms.ELet(id, terms.EIdentifier(value))
            for id, value in substitutions.items()
        ]
        + case.body.body,
    )


k = 0


def fresh():
    global k
    k += 1
    return f"x{k}"


@dataclasses.dataclass
class Leaf:
    body: terms.EDo


@dataclasses.dataclass
class MissingLeaf:
    pass


@dataclasses.dataclass
class Node:
    var: str
    pattern_name: str
    vars: list[str]
    yes: "CaseTree"
    no: "CaseTree"


CaseTree: typing.TypeAlias = Node | MissingLeaf | Leaf


def gen_match(cases1: typing.Sequence[terms.ECase]) -> CaseTree:

    cases = [subst_var_eqs(case) for case in cases1]

    match cases:
        case []:
            return MissingLeaf()
        case [(patterns, body), *_] if not patterns:
            return Leaf(body)
        case [(patterns, body), *_]:
            branch_var = branching_heuristic(patterns, cases)
            branch_pattern = patterns[branch_var]
            yes = list[terms.ECase]()
            no = list[terms.ECase]()

            # vars = [fresh() for _ in branch_pattern.patterns]
            vars = [f"{branch_var}._{i}" for i in range(len(branch_pattern.patterns))]

            for patterns, body in cases:
                case = terms.ECase(dict[str, terms.Pattern](patterns), body)
                match patterns.get(branch_var, None):
                    case None:
                        yes.append(case)
                        no.append(case)
                        pass
                    case terms.EMatchVariant(id, patterns) if id == branch_pattern.id:
                        yes.append(
                            dataclasses.replace(
                                case,
                                patterns={
                                    key: value
                                    for key, value in case.patterns.items()
                                    if key != branch_var
                                }
                                | dict(zip(vars, patterns)),
                            )
                        )
                        pass
                    case terms.EMatchVariant():
                        no.append(case)
                        pass
                    case match:
                        raise TypeError(f"Unsupported pattern: {match}")

            return Node(
                branch_var, branch_pattern.id, vars, gen_match(yes), gen_match(no)
            )
        case _:
            raise TypeError("Unsupported case")


def branching_heuristic(
    patterns: dict[str, terms.EMatchVariant],
    cases: list[tuple[dict[str, terms.EMatchVariant], terms.EDo]],
) -> str:
    return max(
        patterns.keys(),
        key=lambda v: [
            patterns
            for patterns, _ in cases
            if v in patterns  # isinstance(case, terms.EMatchVariant) and
        ],
    )
