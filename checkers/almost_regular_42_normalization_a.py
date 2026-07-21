#!/usr/bin/env python3
"""Independent audit of the fixed-root normalization for an almost-regular band.

This checker deliberately does not import the CNF generator.  It verifies the
edge map, exact unit suffix, identity with an unsymmetrized base CNF, mutation
rejection, and the complement/relabel convention on all labelled six-vertex
graphs in the {2,3} degree band.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import BinaryIO


def digest_bytes(lines: list[bytes]) -> str:
    return hashlib.sha256(b"".join(lines)).hexdigest()


def open_binary(path: Path) -> BinaryIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rb")
    return path.open("rb")


def independent_edge_variable(u: int, v: int) -> int:
    if u == v:
        raise ValueError("loop")
    low, high = (u, v) if u < v else (v, u)
    return high * (high - 1) // 2 + low + 1


def expected_units(order: int, q: int) -> list[bytes]:
    units: list[bytes] = []
    for other in range(1, order):
        variable = other * (other - 1) // 2 + 1
        literal = variable if other <= q else -variable
        units.append(f"{literal} 0\n".encode("ascii"))
    return units


def verify_units(candidate: list[bytes], expected: list[bytes], primary: int) -> None:
    if candidate != expected:
        raise AssertionError("normalization unit suffix mismatch")
    literals = [int(line.split()[0]) for line in candidate]
    if len({abs(literal) for literal in literals}) != len(literals):
        raise AssertionError("normalization units are not on distinct variables")
    if any(abs(literal) > primary for literal in literals):
        raise AssertionError("normalization unit uses an auxiliary variable")


def mutation_gate(expected: list[bytes], primary: int) -> dict[str, bool]:
    mutations: dict[str, list[bytes]] = {}
    mutations["missing_unit"] = expected[:-1]
    mutations["extra_unit"] = expected + [expected[-1]]
    reversed_first = expected[:]
    first = int(reversed_first[0].split()[0])
    reversed_first[0] = f"{-first} 0\n".encode("ascii")
    mutations["reversed_unit"] = reversed_first
    shifted = expected[:]
    second = int(shifted[1].split()[0])
    shifted[1] = f"{second + 1} 0\n".encode("ascii")
    mutations["shifted_root_variable"] = shifted
    auxiliary = expected[:]
    auxiliary[-1] = f"{primary + 1} 0\n".encode("ascii")
    mutations["auxiliary_variable_unit"] = auxiliary
    results: dict[str, bool] = {}
    for name, candidate in mutations.items():
        try:
            verify_units(candidate, expected, primary)
        except AssertionError:
            results[name] = True
        else:
            results[name] = False
    if not all(results.values()):
        raise AssertionError("a normalization mutation escaped detection")
    return results


def coverage_control() -> dict[str, int | bool]:
    n, q = 6, 2
    edges = [(u, v) for v in range(1, n) for u in range(v)]
    total = 1 << len(edges)
    accepted = 0
    complemented = 0
    relabel_checks = 0
    for mask in range(total):
        adjacency = [[False] * n for _ in range(n)]
        for index, (u, v) in enumerate(edges):
            if mask & (1 << index):
                adjacency[u][v] = adjacency[v][u] = True
        degrees = [sum(row) for row in adjacency]
        if not all(value in {q, q + 1} for value in degrees):
            continue
        accepted += 1
        if q not in degrees:
            adjacency = [
                [False if u == v else not adjacency[u][v] for v in range(n)]
                for u in range(n)
            ]
            degrees = [sum(row) for row in adjacency]
            complemented += 1
        roots = [vertex for vertex, degree in enumerate(degrees) if degree == q]
        if not roots:
            raise AssertionError("coverage control found no degree-q root")
        root = roots[0]
        neighbors = [vertex for vertex in range(n) if adjacency[root][vertex]]
        nonneighbors = [vertex for vertex in range(n) if vertex != root and not adjacency[root][vertex]]
        if len(neighbors) != q or len(nonneighbors) != n - 1 - q:
            raise AssertionError("root partition mismatch")
        old_at_new = [root] + neighbors + nonneighbors
        transformed = [
            [adjacency[old_at_new[u]][old_at_new[v]] for v in range(n)]
            for u in range(n)
        ]
        if not all(transformed[0][v] == (1 <= v <= q) for v in range(1, n)):
            raise AssertionError("relabelled root pattern mismatch")
        transformed_degrees = [sum(row) for row in transformed]
        if not all(value in {q, q + 1} for value in transformed_degrees):
            raise AssertionError("relabeling did not preserve degree band")
        relabel_checks += 1
    if total != 32768 or not accepted or relabel_checks != accepted:
        raise AssertionError("coverage-control count mismatch")
    return {
        "labelled_graphs_checked": total,
        "degree_band_graphs": accepted,
        "all_q_plus_one_regular_graphs_complemented": complemented,
        "successful_relabel_checks": relabel_checks,
        "semantic_control_pass": True,
    }


def audit(
    order: int,
    q: int,
    normalized_cnf: Path,
    base_cnf: Path,
    mapping: Path,
    summary_path: Path,
) -> dict[str, object]:
    if order != 2 * q + 2:
        raise ValueError("coverage lemma requires order = 2*q+2")
    primary = order * (order - 1) // 2
    expected_map = [
        f"{independent_edge_variable(low, high)}\t{low}\t{high}"
        for high in range(1, order)
        for low in range(high)
    ]
    if mapping.read_text(encoding="ascii").splitlines() != expected_map:
        raise AssertionError("independently reconstructed primary map mismatch")

    summary = json.loads(summary_path.read_text(encoding="ascii"))
    units = expected_units(order, q)
    expected_unit_hash = digest_bytes(units)
    expected_summary = {
        "order": order,
        "degree_q": q,
        "degree_values": [q, q + 1],
        "primary_variables": primary,
        "fix_root_neighborhood": True,
        "normalization_root": 0,
        "normalization_neighbors": list(range(1, q + 1)),
        "normalization_nonneighbors": list(range(q + 1, order)),
        "normalization_unit_clauses": order - 1,
        "normalization_unit_ledger_sha256": expected_unit_hash,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            raise AssertionError(f"summary field mismatch: {key}")

    normalized_whole = hashlib.sha256()
    base_whole = hashlib.sha256()
    with open_binary(normalized_cnf) as new_stream, open_binary(base_cnf) as base_stream:
        new_header = new_stream.readline()
        base_header = base_stream.readline()
        normalized_whole.update(new_header)
        base_whole.update(base_header)
        expected_new_header = f"p cnf {summary['variables']} {summary['clauses']}\n".encode("ascii")
        if new_header != expected_new_header:
            raise AssertionError("normalized DIMACS header mismatch")
        base_fields = base_header.decode("ascii").split()
        if base_fields[:2] != ["p", "cnf"] or int(base_fields[2]) != summary["variables"]:
            raise AssertionError("base DIMACS header mismatch")
        base_clauses = int(base_fields[3])
        if int(summary["clauses"]) != base_clauses + order - 1:
            raise AssertionError("normalized clause count is not base + order-1")
        compared = 0
        for base_line in base_stream:
            new_line = new_stream.readline()
            if new_line != base_line:
                raise AssertionError(f"normalized body diverges from base at clause {compared + 1}")
            base_whole.update(base_line)
            normalized_whole.update(new_line)
            compared += 1
        suffix = new_stream.readlines()
        for line in suffix:
            normalized_whole.update(line)
    if compared != base_clauses:
        raise AssertionError("base clause count mismatch")
    verify_units(suffix, units, primary)
    mutations = mutation_gate(units, primary)
    return {
        "status": "fixed_root_normalization_audit_pass",
        "scope": f"degree-{{{q},{q + 1}}} graphs on {order} vertices",
        "coverage_lemma": (
            "If a degree-q vertex exists, choose it; otherwise the graph is (q+1)-regular, "
            "and because order=2q+2 its complement is q-regular. Relabel the chosen root "
            "and its q neighbors to 0 and 1..q."
        ),
        "coverage_control": coverage_control(),
        "primary_map_reconstructed_independently": True,
        "unit_literals": [int(line.split()[0]) for line in units],
        "unit_ledger_sha256": expected_unit_hash,
        "base_clause_lines_compared": compared,
        "base_cnf_uncompressed_sha256": base_whole.hexdigest(),
        "normalized_cnf_uncompressed_sha256": normalized_whole.hexdigest(),
        "normalized_formula_exactly_base_plus_units": True,
        "mutation_rejections": mutations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", type=int, required=True)
    parser.add_argument("--degree-q", type=int, required=True)
    parser.add_argument("--normalized-cnf", type=Path, required=True)
    parser.add_argument("--base-cnf", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("report already exists")
    payload = audit(
        args.order,
        args.degree_q,
        args.normalized_cnf,
        args.base_cnf,
        args.map,
        args.summary,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
