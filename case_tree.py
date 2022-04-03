import dataclasses
import typing

import terms


@dataclasses.dataclass(frozen=True)
class Clause:
    patterns: dict[str, terms.Pattern]
    body: terms.Expr = terms.EDo([])


def subst_var_eqs(clause: Clause):
    substitutions = {
        pattern.identifier: id
        for id, pattern in clause.patterns.items()
        if isinstance(pattern, terms.EMatchAs)
    }

    patterns = {
        id: pattern
        for id, pattern in clause.patterns.items()
        if not isinstance(pattern, terms.EMatchAs)
    }
    if not substitutions:
        return patterns, clause.body

    match clause.body:
        case terms.ECall(
            terms.EFn(
                params=[],
                body=terms.EBlock(body),
            ),
            [],
        ):
            return patterns, append_substitutions(substitutions, body)

    return patterns, append_substitutions(substitutions, [clause.body])


def append_substitutions(substitutions: dict[str, str], body: list[terms.Expr]):
    return terms.EDo(
        list[terms.Expr]()
        + [
            terms.ELet(id, terms.EIdentifier(value))
            for id, value in substitutions.items()
        ]
        + body
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


def gen_match(cases: typing.Sequence[terms.ECase]):
    return gen_match2([Clause({"$": case.pattern}, case.body) for case in cases])


def gen_match2(clauses1: typing.Sequence[Clause]) -> CaseTree:

    clauses = [subst_var_eqs(clause) for clause in clauses1]

    match clauses:
        case []:
            return MissingLeaf()
        case [(patterns, body), *_] if not patterns:
            return Leaf(body)
        case [(patterns, body), *_]:
            branch_var = branching_heuristic(patterns, clauses)
            branch_pattern = patterns[branch_var]
            yes = list[Clause]()
            no = list[Clause]()

            # vars = [fresh() for _ in branch_pattern.patterns]
            vars = [f"{branch_var}._{i}" for i in range(len(branch_pattern.patterns))]

            for patterns, body in clauses:
                clause = Clause(dict[str, terms.Pattern](patterns), body)
                match patterns.get(branch_var, None):
                    case None:
                        yes.append(clause)
                        no.append(clause)

                    case terms.EMatchVariant(id, patterns) if id == branch_pattern.id:
                        yes.append(
                            dataclasses.replace(
                                clause,
                                patterns={
                                    key: value
                                    for key, value in clause.patterns.items()
                                    if key != branch_var
                                }
                                | dict(zip(vars, patterns)),
                            )
                        )

                    case terms.EMatchVariant():
                        no.append(clause)

                    case match:
                        raise TypeError(f"Unsupported pattern: {match}")

            return Node(
                branch_var, branch_pattern.id, vars, gen_match2(yes), gen_match2(no)
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
            len(patterns2)
            for patterns2, _ in cases
            if v in patterns2  # isinstance(case, terms.EMatchVariant) and
        ],
    )
