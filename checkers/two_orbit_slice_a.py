#!/usr/bin/env python3
"""Independent Python CNF derivation for an R(5,5) two-orbit slice."""

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


def variable_id(u: int, v: int, second_distance: int) -> int | None:
    index = orbit_index(u, v, 6)
    if index is not None:
        return index + 1
    index = orbit_index(u, v, second_distance)
    if index is not None:
        return ORDER + index + 1
    return None


def derive(matrix: list[list[int]], second_distance: int):
    origins: list[tuple[tuple[int, ...], int, tuple[int, ...], tuple[tuple[int, int, int], ...]]] = []
    all_variable = 0
    for vertices in itertools.combinations(range(ORDER), 5):
        variables: list[int] = []
        fixed: list[tuple[int, int, int]] = []
        for u, v in itertools.combinations(vertices, 2):
            variable = variable_id(u, v, second_distance)
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


def write_outputs(origins, all_variable: int, second_distance: int, cnf: Path, ledger: Path, summary: Path) -> None:
    unique_clauses = sorted({origin[2] for origin in origins})
    cnf.parent.mkdir(parents=True, exist_ok=True)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    summary.parent.mkdir(parents=True, exist_ok=True)
    with cnf.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {2 * ORDER} {len(unique_clauses)}\n")
        for clause in unique_clauses:
            stream.write(" ".join(map(str, clause)) + (" " if clause else "") + "0\n")
    with ledger.open("w", encoding="ascii", newline="\n") as stream:
        for vertices, color, literals, fixed in origins:
            stream.write(
                ",".join(map(str, vertices)) + "|" + str(color) + "|"
                + ",".join(map(str, literals)) + "|"
                + ",".join(f"{u}-{v}={value}" for u, v, value in fixed) + "\n"
            )
    payload = {
        "checker": "python-itertools-direct-five-set-derivation",
        "order": ORDER,
        "second_distance": second_distance,
        "variables": 2 * ORDER,
        "raw_active_origins": len(origins),
        "unique_clauses": len(unique_clauses),
        "all_variable_five_sets": all_variable,
        "maximum_clause_length": max(map(len, unique_clauses), default=0),
        "empty_clause": () in unique_clauses,
    }
    summary.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("second_distance", type=int)
    parser.add_argument("cnf", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()
    if not 1 <= args.second_distance <= 21 or args.second_distance == 6:
        raise ValueError("second distance must be in {1,...,21} minus {6}")
    matrix = parse_matrix(args.matrix)
    origins, all_variable = derive(matrix, args.second_distance)
    write_outputs(origins, all_variable, args.second_distance, args.cnf, args.ledger, args.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
