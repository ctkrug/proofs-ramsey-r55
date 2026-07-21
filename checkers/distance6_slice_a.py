#!/usr/bin/env python3
"""Exact Z3 checker for the 43-variable distance-six slice of the R55 seed."""

from __future__ import annotations

import argparse
from collections import Counter
import itertools
import json
from pathlib import Path

from z3 import Bool, If, Not, Or, Solver, Sum, sat, unsat


ORDER = 43
TITLE = "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"


def parse_raw(path: Path) -> list[list[int]]:
    raw = path.read_bytes()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("publisher matrix is not ASCII") from error
    if not text.endswith("\n"):
        raise ValueError("publisher matrix lacks its final LF")
    lines = text.splitlines()
    if len(lines) != ORDER + 1 or lines[0] != TITLE:
        raise ValueError("publisher title or row count mismatch")
    matrix = []
    for row_number, line in enumerate(lines[1:]):
        tokens = line.split(" ")
        if len(tokens) != ORDER or any(token not in {"0", "1"} for token in tokens):
            raise ValueError(f"row {row_number} is not exactly 43 single-space-delimited bits")
        matrix.append([int(token) for token in tokens])
    for u in range(ORDER):
        if matrix[u][u]:
            raise ValueError("matrix diagonal must be zero")
        for v in range(u + 1, ORDER):
            if matrix[u][v] != matrix[v][u]:
                raise ValueError("matrix must be symmetric")
    return matrix


def distance6_variable(u: int, v: int) -> int | None:
    difference = v - u
    if difference == 6:
        return u
    if difference == ORDER - 6:
        return v
    return None


def derive_constraints(
    matrix: list[list[int]],
) -> tuple[list[tuple[int, tuple[int, ...]]], list[dict[str, object]]]:
    raw_constraints: list[tuple[int, tuple[int, ...]]] = []
    active_five_sets: list[dict[str, object]] = []
    for vertices in itertools.combinations(range(ORDER), 5):
        variables: list[int] = []
        fixed: list[int] = []
        for u, v in itertools.combinations(vertices, 2):
            variable = distance6_variable(u, v)
            if variable is None:
                fixed.append(matrix[u][v])
            else:
                variables.append(variable)
        variables_tuple = tuple(sorted(variables))
        if fixed and not any(fixed):
            raw_constraints.append((1, variables_tuple))
            active_five_sets.append({"color": 0, "vertices": list(vertices), "variables": list(variables_tuple)})
        if fixed and all(fixed):
            raw_constraints.append((0, variables_tuple))
            active_five_sets.append({"color": 1, "vertices": list(vertices), "variables": list(variables_tuple)})
    return raw_constraints, active_five_sets


def normalized_shape(variables: tuple[int, ...]) -> tuple[int, ...]:
    # 8 is the inverse of 27 modulo 43.  Coordinate t therefore means
    # original vertex u = 27*t mod 43.
    transformed = tuple((8 * variable) % ORDER for variable in variables)
    return min(tuple(sorted((value - anchor) % ORDER for value in transformed)) for anchor in transformed)


def is_cyclic_interval(word: tuple[bool, ...], length: int) -> bool:
    transformed = [word[(27 * index) % ORDER] for index in range(ORDER)]
    transitions = sum(transformed[index] != transformed[(index + 1) % ORDER] for index in range(ORDER))
    return sum(transformed) == length and transitions == 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    args = parser.parse_args()
    matrix = parse_raw(args.matrix)
    raw_constraints, active_five_sets = derive_constraints(matrix)
    multiplicities = Counter(raw_constraints)
    positive_pairs = sorted(
        {variables for (positive, variables), count in multiplicities.items() if positive and count == 2}
    )
    negative_triples = sorted(
        {variables for (positive, variables), count in multiplicities.items() if not positive and count == 1}
    )
    if len(raw_constraints) != 215 or len(positive_pairs) != 86 or len(negative_triples) != 43:
        raise AssertionError("unexpected reduced-constraint cardinality")
    if set(multiplicities.values()) != {1, 2}:
        raise AssertionError("unexpected active-five-set multiplicity")

    variables = [Bool(f"edge_{u}_{(u + 6) % ORDER}") for u in range(ORDER)]
    expressions = []
    for positive, indices in raw_constraints:
        literals = [variables[index] if positive else Not(variables[index]) for index in indices]
        expressions.append(Or(*literals))
    violations = [If(expression, 0, 1) for expression in expressions]

    bounds: dict[str, str] = {}
    for bound in (0, 1):
        solver = Solver()
        solver.add(Sum(violations) <= bound)
        result = solver.check()
        if result != unsat:
            raise AssertionError(f"distance-six slice unexpectedly has a burden <= {bound} assignment")
        bounds[str(bound)] = str(result)

    solver = Solver()
    solver.add(Sum(violations) <= 2)
    words: set[str] = set()
    while solver.check() == sat:
        model = solver.model()
        word_tuple = tuple(bool(model.eval(variable, model_completion=True)) for variable in variables)
        word = "".join("1" if bit else "0" for bit in word_tuple)
        words.add(word)
        solver.add(Or(*[variable != word_tuple[index] for index, variable in enumerate(variables)]))
    if len(words) != 86:
        raise AssertionError("unexpected number of optimum distance-six words")

    classifications = Counter()
    for word in words:
        word_tuple = tuple(bit == "1" for bit in word)
        burden = sum(
            (not any(word_tuple[index] for index in indices))
            if positive
            else all(word_tuple[index] for index in indices)
            for positive, indices in raw_constraints
        )
        if burden != 2:
            raise AssertionError("enumerated word does not have burden exactly two")
        if is_cyclic_interval(word_tuple, 24):
            classifications["step27_cyclic_interval_length_24"] += 1
        elif is_cyclic_interval(word_tuple, 25):
            classifications["step27_cyclic_interval_length_25"] += 1
        else:
            raise AssertionError("optimum word is outside the admitted interval classification")

    result = {
        "checker": "python-z3-pseudo-boolean-enumeration",
        "order": ORDER,
        "variable_family": "the 43 edges {u,u+6 mod 43}; all other cyclic-distance edges frozen",
        "coordinate": "t with u=27*t mod 43",
        "raw_active_five_sets": len(raw_constraints),
        "unique_constraints": len(multiplicities),
        "positive_pairs": [list(item) for item in positive_pairs],
        "positive_pair_multiplicity": 2,
        "negative_triples": [list(item) for item in negative_triples],
        "negative_triple_multiplicity": 1,
        "normal_form": {
            "positive_pair_shapes": [list(item) for item in sorted({normalized_shape(item) for item in positive_pairs})],
            "negative_triple_shapes": [list(item) for item in sorted({normalized_shape(item) for item in negative_triples})],
        },
        "burden_at_most": {**bounds, "2": "sat"},
        "minimum_burden": 2,
        "minimum_model_count": len(words),
        "minimum_model_classification": dict(sorted(classifications.items())),
        "minimum_words_u_order": sorted(words),
        "active_five_sets": active_five_sets,
    }
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
