#!/usr/bin/env python3
"""Deterministic Ramsey CNF with Sinz degree-band constraints.

Primary variable ``edge_var(u,v)`` is true exactly when {u,v} is an edge.
The ordering is graph6's upper-triangle ordering: high first, then low.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Iterable, TextIO


def edge_var(u: int, v: int) -> int:
    if u == v:
        raise ValueError("loops have no edge variable")
    low, high = sorted((u, v))
    return high * (high - 1) // 2 + low + 1


def at_most_counts(number: int, bound: int) -> tuple[int, int]:
    if bound < 0:
        return 0, 1
    if bound >= number:
        return 0, 0
    if bound == 0:
        return 0, number
    return (number - 1) * bound, 2 * bound * number - 3 * bound + number - 1


def emit_at_most(
    stream: TextIO, literals: list[int], bound: int, next_variable: int
) -> tuple[int, int]:
    """Emit Sinz's sequential at-most-k encoding; return next var and clauses."""
    number = len(literals)
    auxiliary, expected_clauses = at_most_counts(number, bound)
    if bound < 0:
        stream.write("0\n")
        return next_variable, 1
    if bound >= number:
        return next_variable, 0
    if bound == 0:
        for literal in literals:
            stream.write(f"{-literal} 0\n")
        return next_variable, number

    start = next_variable

    def sequential(i: int, j: int) -> int:
        # i ranges 1..number-1 and j ranges 1..bound.
        return start + (i - 1) * bound + (j - 1)

    clauses = 0
    stream.write(f"{-literals[0]} {sequential(1, 1)} 0\n")
    clauses += 1
    for j in range(2, bound + 1):
        stream.write(f"{-sequential(1, j)} 0\n")
        clauses += 1
    for i in range(2, number):
        stream.write(f"{-literals[i - 1]} {sequential(i, 1)} 0\n")
        stream.write(f"{-sequential(i - 1, 1)} {sequential(i, 1)} 0\n")
        clauses += 2
        for j in range(2, bound + 1):
            stream.write(
                f"{-literals[i - 1]} {-sequential(i - 1, j - 1)} {sequential(i, j)} 0\n"
            )
            stream.write(f"{-sequential(i - 1, j)} {sequential(i, j)} 0\n")
            clauses += 2
    for i in range(2, number + 1):
        stream.write(f"{-literals[i - 1]} {-sequential(i - 1, bound)} 0\n")
        clauses += 1
    if clauses != expected_clauses:
        raise AssertionError((clauses, expected_clauses))
    return next_variable + auxiliary, clauses


def ramsey_clause_lines(order: int, clique_size: int) -> Iterable[str]:
    for vertices in itertools.combinations(range(order), clique_size):
        variables = [edge_var(u, v) for u, v in itertools.combinations(vertices, 2)]
        yield " ".join(map(str, variables)) + " 0\n"  # forbid an independent set
        yield " ".join(map(str, (-variable for variable in variables))) + " 0\n"  # forbid a clique


def generate(
    order: int,
    clique_size: int,
    degree_q: int | None,
    cnf_path: Path,
    map_path: Path,
    summary_path: Path,
) -> dict[str, object]:
    if order < 1 or not 2 <= clique_size <= order:
        raise ValueError("invalid order or clique size")
    if degree_q is not None and not 0 <= degree_q < order:
        raise ValueError("degree q must be in 0..order-1")
    primary = order * (order - 1) // 2
    ramsey_clauses = 2 * math.comb(order, clique_size)
    next_variable = primary + 1
    degree_clauses = 0
    degree_auxiliary = 0
    if degree_q is not None:
        for bound in (degree_q + 1, order - 1 - degree_q):
            auxiliary, clauses = at_most_counts(order - 1, bound)
            degree_auxiliary += order * auxiliary
            degree_clauses += order * clauses
    variables = primary + degree_auxiliary
    clauses = ramsey_clauses + degree_clauses

    for path in (cnf_path, map_path, summary_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    ledger_hash = hashlib.sha256()
    with cnf_path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {variables} {clauses}\n")
        for line in ramsey_clause_lines(order, clique_size):
            stream.write(line)
            ledger_hash.update(line.encode("ascii"))
        if degree_q is not None:
            for vertex in range(order):
                incident = [edge_var(vertex, other) for other in range(order) if other != vertex]
                before = next_variable
                next_variable, emitted = emit_at_most(stream, incident, degree_q + 1, next_variable)
                degree_clauses -= emitted
                degree_auxiliary -= next_variable - before
                before = next_variable
                next_variable, emitted = emit_at_most(
                    stream, [-literal for literal in incident], order - 1 - degree_q, next_variable
                )
                degree_clauses -= emitted
                degree_auxiliary -= next_variable - before
    if next_variable != variables + 1 or degree_clauses or degree_auxiliary:
        raise AssertionError("counter accounting mismatch")

    with map_path.open("w", encoding="ascii", newline="\n") as stream:
        for high in range(1, order):
            for low in range(high):
                stream.write(f"{edge_var(low, high)}\t{low}\t{high}\n")
    payload: dict[str, object] = {
        "checker": "python-itertools-sinz-sequential-counter",
        "order": order,
        "clique_size": clique_size,
        "degree_q": degree_q,
        "degree_values": None if degree_q is None else [degree_q, degree_q + 1],
        "primary_variables": primary,
        "variables": variables,
        "ramsey_clauses": ramsey_clauses,
        "degree_clauses": clauses - ramsey_clauses,
        "clauses": clauses,
        "ramsey_ledger_sha256": ledger_hash.hexdigest(),
    }
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="ascii")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", type=int, required=True)
    parser.add_argument("--clique-size", type=int, required=True)
    parser.add_argument("--degree-q", type=int)
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    generate(args.order, args.clique_size, args.degree_q, args.cnf, args.map, args.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
