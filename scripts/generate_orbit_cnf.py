#!/usr/bin/env python3
"""Generate deterministic Ramsey CNFs for released cyclic-distance orbits.

The generator is self-contained and does not import retained R55 code.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import itertools
import json
from pathlib import Path


N = 43
TITLE = "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"


class CNF:
    def __init__(self, initial_variables: int) -> None:
        self.variable_count = initial_variables
        self.clauses: list[list[int]] = []

    def new_variable(self) -> int:
        self.variable_count += 1
        return self.variable_count

    def add(self, *literals: int) -> None:
        self.clauses.append(list(literals))


def parse_matrix(path: Path) -> list[list[int]]:
    raw = path.read_bytes()
    if not raw.endswith(b"\n"):
        raise ValueError("matrix lacks final LF")
    lines = raw.decode("ascii").splitlines()
    if len(lines) != N + 1 or lines[0] != TITLE:
        raise ValueError("title or row count mismatch")
    matrix: list[list[int]] = []
    for line in lines[1:]:
        fields = line.split()
        if len(fields) != N or any(field not in {"0", "1"} for field in fields):
            raise ValueError("invalid matrix row")
        matrix.append([int(field) for field in fields])
    for u in range(N):
        if matrix[u][u] != 0:
            raise ValueError("nonzero diagonal")
        for v in range(u + 1, N):
            if matrix[u][v] != matrix[v][u]:
                raise ValueError("asymmetric matrix")
    return matrix


def orbit_edge_start(u: int, v: int, distance: int) -> int | None:
    delta = (v - u) % N
    if delta == distance:
        return u
    if delta == N - distance:
        return v
    return None


def base_variable(orbit_index: int, start: int) -> int:
    return orbit_index * N + start + 1


def derive_raw_clauses(matrix: list[list[int]], distances: list[int]) -> tuple[list[list[int]], list[dict[str, object]], Counter[str]]:
    raw_clauses: list[list[int]] = []
    active: list[dict[str, object]] = []
    accounting: Counter[str] = Counter()
    for vertices in itertools.combinations(range(N), 5):
        accounting["five_sets_examined"] += 1
        variable_ids: list[int] = []
        fixed: list[int] = []
        for u, v in itertools.combinations(vertices, 2):
            found: tuple[int, int] | None = None
            for orbit_index, distance in enumerate(distances):
                start = orbit_edge_start(u, v, distance)
                if start is not None:
                    if found is not None:
                        raise AssertionError("released edge belongs to two distance orbits")
                    found = (orbit_index, start)
            if found is None:
                fixed.append(matrix[u][v])
            else:
                variable_ids.append(base_variable(*found))
        variables = sorted(variable_ids)
        zero_possible = 1 not in fixed
        one_possible = 0 not in fixed
        if zero_possible:
            raw_clauses.append(variables)
            active.append({"vertices": list(vertices), "color": 0, "clause": variables})
            accounting["zero_active"] += 1
        if one_possible:
            raw_clauses.append([-variable for variable in variables])
            active.append({"vertices": list(vertices), "color": 1, "clause": [-variable for variable in variables]})
            accounting["one_active"] += 1
        if not zero_possible and not one_possible:
            accounting["inactive_fixed_both_colors"] += 1
        elif zero_possible and one_possible:
            accounting["double_active_no_fixed_edges"] += 1
        else:
            accounting["single_active"] += 1
    if accounting["five_sets_examined"] != 962_598:
        raise AssertionError("C(43,5) accounting mismatch")
    return raw_clauses, active, accounting


def add_at_most(cnf: CNF, variables: list[int], maximum: int) -> dict[str, int]:
    if maximum < 0:
        cnf.add()
        return {"counter_variables": 0, "counter_clauses": 1}
    if maximum >= len(variables):
        return {"counter_variables": 0, "counter_clauses": 0}
    before_variables = cnf.variable_count
    before_clauses = len(cnf.clauses)
    if maximum == 0:
        for variable in variables:
            cnf.add(-variable)
        return {
            "counter_variables": cnf.variable_count - before_variables,
            "counter_clauses": len(cnf.clauses) - before_clauses,
        }

    # Sinz-style sequential counter. s[i][j] means at least j of x[0..i]
    # are true. The implications below are sufficient and equisatisfiable.
    counter = [[cnf.new_variable() for _ in range(maximum)] for _ in variables]
    cnf.add(-variables[0], counter[0][0])
    for j in range(1, maximum):
        cnf.add(-counter[0][j])
    for i in range(1, len(variables)):
        cnf.add(-variables[i], counter[i][0])
        for j in range(maximum):
            cnf.add(-counter[i - 1][j], counter[i][j])
        for j in range(1, maximum):
            cnf.add(-variables[i], -counter[i - 1][j - 1], counter[i][j])
        cnf.add(-variables[i], -counter[i - 1][maximum - 1])
    return {
        "counter_variables": cnf.variable_count - before_variables,
        "counter_clauses": len(cnf.clauses) - before_clauses,
    }


def add_at_most_combinatorial(cnf: CNF, variables: list[int], maximum: int) -> dict[str, int]:
    before_clauses = len(cnf.clauses)
    if maximum < 0:
        cnf.add()
    elif maximum < len(variables):
        for forbidden in itertools.combinations(variables, maximum + 1):
            cnf.add(*[-variable for variable in forbidden])
    return {
        "counter_variables": 0,
        "counter_clauses": len(cnf.clauses) - before_clauses,
    }


def add_prefix_equivalence(cnf: CNF, previous: int | None, left: int, right: int) -> int:
    current = cnf.new_variable()
    if previous is not None:
        cnf.add(-current, previous)
    cnf.add(-current, -left, right)
    cnf.add(-current, left, -right)
    if previous is None:
        cnf.add(left, right, current)
        cnf.add(-left, -right, current)
    else:
        cnf.add(-previous, left, right, current)
        cnf.add(-previous, -left, -right, current)
    return current


def add_rotation_lex_leader(cnf: CNF, distances: list[int]) -> dict[str, int]:
    before_variables = cnf.variable_count
    before_clauses = len(cnf.clauses)
    word = [base_variable(orbit_index, u) for orbit_index in range(len(distances)) for u in range(N)]
    for shift in range(1, N):
        shifted = [
            base_variable(orbit_index, (u + shift) % N)
            for orbit_index in range(len(distances))
            for u in range(N)
        ]
        previous: int | None = None
        for index, (left, right) in enumerate(zip(word, shifted, strict=True)):
            if previous is None:
                cnf.add(-left, right)
            else:
                cnf.add(-previous, -left, right)
            if index + 1 < len(word):
                previous = add_prefix_equivalence(cnf, previous, left, right)
    return {
        "lex_variables": cnf.variable_count - before_variables,
        "lex_clauses": len(cnf.clauses) - before_clauses,
    }


def min_fill_width(raw_clauses: list[list[int]], base_count: int) -> int:
    adjacency = {variable: set() for variable in range(1, base_count + 1)}
    for clause in raw_clauses:
        variables = sorted({abs(literal) for literal in clause})
        for left, right in itertools.combinations(variables, 2):
            adjacency[left].add(right)
            adjacency[right].add(left)
    width = 0
    while adjacency:
        def key(variable: int) -> tuple[int, int, int]:
            neighbors = adjacency[variable]
            missing = sum(1 for left, right in itertools.combinations(neighbors, 2) if right not in adjacency[left])
            return missing, len(neighbors), variable

        selected = min(adjacency, key=key)
        neighbors = list(adjacency[selected])
        width = max(width, len(neighbors))
        for left, right in itertools.combinations(neighbors, 2):
            adjacency[left].add(right)
            adjacency[right].add(left)
        for neighbor in neighbors:
            adjacency[neighbor].discard(selected)
        del adjacency[selected]
    return width


def write_cnf(path: Path, cnf: CNF) -> None:
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {cnf.variable_count} {len(cnf.clauses)}\n")
        for clause in cnf.clauses:
            stream.write(" ".join(map(str, clause)) + (" " if clause else "") + "0\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("output_cnf", type=Path)
    parser.add_argument("output_metadata", type=Path)
    parser.add_argument("--distances", required=True, help="comma-separated values in 1..21")
    parser.add_argument("--max-burden", type=int, default=0)
    parser.add_argument("--cardinality-encoding", choices=("sequential", "combinatorial"), default="sequential")
    parser.add_argument("--rotation-lex-leader", action="store_true")
    parser.add_argument("--block-words", type=Path)
    parser.add_argument("--require-orbit-change", type=int, action="append", default=[])
    args = parser.parse_args()

    distances = [int(item) for item in args.distances.split(",")]
    if not distances or len(set(distances)) != len(distances) or any(not 1 <= item <= 21 for item in distances):
        raise ValueError("distances must be distinct values in 1..21")
    matrix = parse_matrix(args.matrix)
    raw_clauses, active, accounting = derive_raw_clauses(matrix, distances)
    base_count = len(distances) * N
    cnf = CNF(base_count)
    relaxation_variables: list[int] = []
    if args.max_burden == 0:
        for clause in raw_clauses:
            cnf.add(*clause)
        cardinality = {"counter_variables": 0, "counter_clauses": 0}
    else:
        for clause in raw_clauses:
            relaxation = cnf.new_variable()
            relaxation_variables.append(relaxation)
            cnf.add(*clause, relaxation)
        if args.cardinality_encoding == "combinatorial":
            cardinality = add_at_most_combinatorial(cnf, relaxation_variables, args.max_burden)
        else:
            cardinality = add_at_most(cnf, relaxation_variables, args.max_burden)

    symmetry = {"lex_variables": 0, "lex_clauses": 0}
    if args.rotation_lex_leader:
        symmetry = add_rotation_lex_leader(cnf, distances)

    orbit_change_clauses: list[list[int]] = []
    for orbit_index in args.require_orbit_change:
        if not 0 <= orbit_index < len(distances):
            raise ValueError("required changed orbit index is out of range")
        distance = distances[orbit_index]
        clause = []
        for u in range(N):
            variable = base_variable(orbit_index, u)
            base_value = matrix[u][(u + distance) % N]
            clause.append(variable if base_value == 0 else -variable)
        cnf.add(*clause)
        orbit_change_clauses.append(clause)

    blocked_words: list[str] = []
    if args.block_words is not None:
        blocked_words = json.loads(args.block_words.read_text(encoding="utf-8"))
        for word in blocked_words:
            if len(word) != base_count or any(bit not in "01" for bit in word):
                raise ValueError("invalid blocked word")
            cnf.add(*[-(index + 1) if bit == "1" else index + 1 for index, bit in enumerate(word)])

    args.output_cnf.parent.mkdir(parents=True, exist_ok=True)
    args.output_metadata.parent.mkdir(parents=True, exist_ok=True)
    write_cnf(args.output_cnf, cnf)
    clause_lengths = Counter(map(len, raw_clauses))
    occurrences = Counter(abs(literal) for clause in raw_clauses for literal in clause)
    unique_raw = {tuple(clause) for clause in raw_clauses}
    metadata = {
        "schema_version": 1,
        "generator": "self-contained all-C(43,5) cyclic-orbit CNF generator",
        "matrix_path": str(args.matrix),
        "matrix_sha256": sha256(args.matrix.read_bytes()).hexdigest(),
        "distances": distances,
        "base_variables": base_count,
        "variable_mapping": "1 + 43*orbit_index + u encodes edge {u,u+distance[orbit_index] mod 43}",
        "max_burden": args.max_burden,
        "cardinality_encoding": args.cardinality_encoding if args.max_burden else "none",
        "raw_active_five_sets": len(raw_clauses),
        "unique_raw_clauses": len(unique_raw),
        "five_set_accounting": dict(accounting),
        "raw_clause_length_histogram": dict(sorted(clause_lengths.items())),
        "base_variable_occurrence_min": min(occurrences.values(), default=0),
        "base_variable_occurrence_max": max(occurrences.values(), default=0),
        "primal_min_fill_width_upper_bound": min_fill_width(raw_clauses, base_count),
        "relaxation_variables": len(relaxation_variables),
        "cardinality": cardinality,
        "rotation_lex_leader": args.rotation_lex_leader,
        "symmetry": {
            **symmetry,
            "group": "common Z_43 rotation on all released edge orbits",
            "coverage_argument": "every finite common-rotation orbit contains a lexicographically least concatenated orbit word; the CNF admits exactly the least word(s), including periodic ties",
        },
        "blocked_base_words": len(blocked_words),
        "required_changed_orbit_indices": args.require_orbit_change,
        "orbit_change_clause_count": len(orbit_change_clauses),
        "cnf_variables": cnf.variable_count,
        "cnf_clauses": len(cnf.clauses),
        "cnf_path": str(args.output_cnf),
        "cnf_sha256": sha256(args.output_cnf.read_bytes()).hexdigest(),
        "active_five_sets_sha256": sha256(json.dumps(active, separators=(",", ":"), sort_keys=True).encode()).hexdigest(),
    }
    args.output_metadata.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
