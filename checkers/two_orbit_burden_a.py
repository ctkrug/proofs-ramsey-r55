#!/usr/bin/env python3
"""Python raw-origin encoding for burden <= 1 in R55 orbit slices.

Mode 0 frees only cyclic distance 6.  Mode d in {1,...,21} minus {6}
frees cyclic distances 6 and d.  Every active five-set/color origin receives
its own relaxation variable; duplicate graph clauses are never merged.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path


ORDER = 43
TITLE = "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"
EXPECTED_SHA256 = "c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990"


def parse_matrix(path: Path) -> list[list[int]]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise ValueError("publisher matrix SHA-256 mismatch")
    try:
        lines = raw.decode("ascii").splitlines(keepends=True)
    except UnicodeDecodeError as error:
        raise ValueError("publisher matrix is not ASCII") from error
    if len(lines) != ORDER + 1 or lines[0] != TITLE + "\n":
        raise ValueError("publisher title, line ending, or row count mismatch")
    matrix: list[list[int]] = []
    for row, line in enumerate(lines[1:]):
        if not line.endswith("\n"):
            raise ValueError("publisher row lacks final LF")
        tokens = line[:-1].split(" ")
        if len(tokens) != ORDER or any(token not in {"0", "1"} for token in tokens):
            raise ValueError(f"publisher row {row} is not 43 single-space-delimited bits")
        matrix.append([int(token) for token in tokens])
    for u in range(ORDER):
        if matrix[u][u] != 0:
            raise ValueError("matrix diagonal is nonzero")
        for v in range(u + 1, ORDER):
            if matrix[u][v] != matrix[v][u]:
                raise ValueError("matrix is asymmetric")
    return matrix


def orbit_index(u: int, v: int, distance: int) -> int | None:
    difference = v - u
    if difference == distance:
        return u
    if difference == ORDER - distance:
        return v
    return None


def variable_id(u: int, v: int, mode: int) -> int | None:
    index = orbit_index(u, v, 6)
    if index is not None:
        return index + 1
    if mode:
        index = orbit_index(u, v, mode)
        if index is not None:
            return ORDER + index + 1
    return None


def derive(matrix: list[list[int]], mode: int):
    origins: list[tuple[tuple[int, ...], int, tuple[int, ...], tuple[tuple[int, int, int], ...]]] = []
    all_variable = 0
    for vertices in itertools.combinations(range(ORDER), 5):
        variables: list[int] = []
        fixed: list[tuple[int, int, int]] = []
        for u, v in itertools.combinations(vertices, 2):
            variable = variable_id(u, v, mode)
            if variable is None:
                fixed.append((u, v, matrix[u][v]))
            else:
                variables.append(variable)
        if not fixed:
            all_variable += 1
        for color in (0, 1):
            if any(value != color for _, _, value in fixed):
                continue
            literals = tuple(sorted(variable if color == 0 else -variable for variable in variables))
            origins.append((vertices, color, literals, tuple(fixed)))
    return origins, all_variable


def prefix_amo(relaxation_variables: list[int], first_auxiliary: int) -> tuple[int, list[tuple[int, ...]]]:
    """Sinz-style prefix AMO; auxiliaries s_i represent some r_1..r_i."""
    count = len(relaxation_variables)
    if count <= 1:
        return first_auxiliary - 1, []
    auxiliaries = [first_auxiliary + index for index in range(count - 1)]
    clauses: list[tuple[int, ...]] = [(-relaxation_variables[0], auxiliaries[0])]
    for index in range(1, count - 1):
        clauses.extend((
            (-relaxation_variables[index], auxiliaries[index]),
            (-auxiliaries[index - 1], auxiliaries[index]),
            (-relaxation_variables[index], -auxiliaries[index - 1]),
        ))
    clauses.append((-relaxation_variables[-1], -auxiliaries[-1]))
    return auxiliaries[-1], clauses


def write_outputs(origins, all_variable: int, mode: int, cnf: Path, ledger: Path,
                  mapping: Path, summary: Path) -> None:
    graph_variables = ORDER if mode == 0 else 2 * ORDER
    origin_count = len(origins)
    relaxation_variables = [graph_variables + index + 1 for index in range(origin_count)]
    maximum_variable, amo_clauses = prefix_amo(
        relaxation_variables, graph_variables + origin_count + 1
    )
    relaxed_clauses = [origin[2] + (relaxation_variables[index],) for index, origin in enumerate(origins)]
    clauses = relaxed_clauses + amo_clauses
    for path in (cnf, ledger, mapping, summary):
        path.parent.mkdir(parents=True, exist_ok=True)
    with cnf.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {maximum_variable} {len(clauses)}\n")
        for clause in clauses:
            stream.write(" ".join(map(str, clause)) + (" " if clause else "") + "0\n")
    with ledger.open("w", encoding="ascii", newline="\n") as stream:
        for vertices, color, literals, fixed in origins:
            stream.write(
                ",".join(map(str, vertices)) + "|" + str(color) + "|"
                + ",".join(map(str, literals)) + "|"
                + ",".join(f"{u}-{v}={value}" for u, v, value in fixed) + "\n"
            )
    with mapping.open("w", encoding="ascii", newline="\n") as stream:
        for index, (origin, relaxation) in enumerate(zip(origins, relaxation_variables), 1):
            vertices, color, _literals, _fixed = origin
            stream.write(f"{index}|{relaxation}|{','.join(map(str, vertices))}|{color}\n")
    payload = {
        "checker": "python-itertools-prefix-sequential-amo",
        "order": ORDER,
        "mode": mode,
        "graph_variables": graph_variables,
        "raw_active_origins": origin_count,
        "relaxation_variables": origin_count,
        "auxiliary_variables": max(0, origin_count - 1),
        "variables": maximum_variable,
        "relaxed_origin_clauses": origin_count,
        "amo_clauses": len(amo_clauses),
        "clauses": len(clauses),
        "all_variable_five_sets": all_variable,
        "maximum_origin_clause_length": max((len(origin[2]) for origin in origins), default=0),
        "cardinality_bound": 1,
        "cardinality_encoding": "prefix sequential AMO",
        "duplicates_preserved": True,
    }
    summary.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("mode", type=int, help="0 for distance 6 only; otherwise second distance")
    parser.add_argument("cnf", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("mapping", type=Path)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()
    if args.mode != 0 and (not 1 <= args.mode <= 21 or args.mode == 6):
        raise ValueError("mode must be 0 or in {1,...,21} minus {6}")
    matrix = parse_matrix(args.matrix)
    origins, all_variable = derive(matrix, args.mode)
    write_outputs(origins, all_variable, args.mode, args.cnf, args.ledger, args.mapping, args.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
