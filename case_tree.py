import dataclasses
import typing

import terms


@dataclasses.dataclass(frozen=True)
class Clause:
    patterns: dict[str, terms.EPattern]
    body: terms.EDo = dataclasses.field(default_factory=terms.EDo)


def subst_var_eqs(clause: Clause):
    substitutions = {
        pattern.pattern.identifier: id
        for id, pattern in clause.patterns.items()
        if isinstance(pattern.pattern, terms.EMatchAs)
    }

    patterns = {
        id: pattern.pattern
        for id, pattern in clause.patterns.items()
        if not isinstance(pattern.pattern, terms.EMatchAs)
    }

    return patterns, terms.EDo(
        block=terms.EBlock(
            list[terms.EExpr]()
            + [
                terms.EExpr ** terms.ELet(id, terms.EExpr ** terms.EIdentifier(value))
                for id, value in substitutions.items()
            ]
            + clause.body.block.body
        ),
        hint=clause.body.hint,
    )


# k = 0


# def fresh():
#     global k
#     k += 1
#     return f"x{k}"


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

    if len(clauses) < 1:
        return MissingLeaf()

    patterns, body = clauses[0]

    if not patterns:
        return Leaf(body)

    branch_var = branching_heuristic(patterns, clauses)
    branch_pattern = patterns[branch_var]
    yes = list[Clause]()
    no = list[Clause]()

    # vars = [fresh() for _ in branch_pattern.patterns]
    vars = [f"{branch_var}._{i}" for i in range(len(branch_pattern.patterns))]

    for patterns2, body2 in clauses:
        clause = Clause(
            dict[str, terms.EPattern](
                {key: terms.EPattern(pattern) for key, pattern in patterns2.items()}
            ),
            body2,
        )
        match patterns2.get(branch_var, None):
            case None:
                yes.append(clause)
                no.append(clause)

            case terms.EMatchVariant(id, patterns2) if id == branch_pattern.id:
                yes.append(
                    Clause(
                        body=body2,
                        patterns={
                            key: value
                            for key, value in clause.patterns.items()
                            if key != branch_var
                        }
                        | dict(zip(vars, patterns2)),
                    )
                )

            case terms.EMatchVariant():
                no.append(clause)

            case match:
                raise TypeError(f"Unsupported pattern: {match}")

    return Node(branch_var, branch_pattern.id, vars, gen_match2(yes), gen_match2(no))


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
