#!/usr/bin/env python3
"""Cold audit of the record-21 destroy-label quotient packet.

This checker imports no producer code.  It independently reconstructs the
boundary mapping and expected raw Ramsey clauses, evaluates the physical CNF,
checks the source block, and validates a SAT graph with NetworkX.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import sys

import networkx as nx


ORDER = 42
SOURCE_RECORD = 21
FINGERPRINT = "r55novel42basin2026"
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def destroy_set() -> list[int]:
    ranked = sorted(
        range(ORDER),
        key=lambda vertex: hashlib.sha256(
            f"{FINGERPRINT}:destroy:{SOURCE_RECORD - 1}:{vertex}".encode()
        ).digest(),
    )
    return sorted(ranked[:12])


def parse_dimacs(path: Path) -> tuple[int, list[tuple[int, ...]]]:
    variables = declared_clauses = None
    clauses: list[tuple[int, ...]] = []
    for line_number, raw in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        if not raw or raw.startswith("c"):
            continue
        if raw.startswith("p cnf "):
            _, _, variable_text, clause_text = raw.split()
            variables, declared_clauses = int(variable_text), int(clause_text)
            continue
        literals = [int(text) for text in raw.split()]
        if not literals or literals[-1] != 0:
            raise AssertionError(f"malformed DIMACS line {line_number}")
        clause = tuple(literals[:-1])
        if not clause or any(abs(literal) > (variables or 0) for literal in clause):
            raise AssertionError("empty or out-of-range DIMACS clause")
        clauses.append(clause)
    if variables is None or declared_clauses != len(clauses):
        raise AssertionError("DIMACS header mismatch")
    return variables, clauses


def reconstruct_raw(source: nx.Graph, destroy: list[int], edges: list[tuple[int, int]]) -> list[tuple[int, ...]]:
    edge_number = {edge: index + 1 for index, edge in enumerate(edges)}
    core = set(range(ORDER)).difference(destroy)
    result: list[tuple[int, ...]] = []
    for five in itertools.combinations(range(ORDER), 5):
        if set(five).issubset(core):
            continue
        boundary: list[int] = []
        core_colours: list[bool] = []
        for pair in itertools.combinations(five, 2):
            edge = tuple(sorted(pair))
            number = edge_number.get(edge)
            if number is None:
                core_colours.append(source.has_edge(*edge))
            else:
                boundary.append(number)
        if False not in core_colours:
            result.append(tuple(-number for number in boundary))
        if True not in core_colours:
            result.append(tuple(boundary))
    return result


def clause_true(clause: tuple[int, ...], values: dict[int, bool]) -> bool:
    return any(values[abs(literal)] is (literal > 0) for literal in clause)


def expected_prefix_values(values: dict[int, bool], row_pairs: list[tuple[list[int], list[int], list[int]]]) -> dict[int, bool]:
    completed = dict(values)
    for left, right, auxiliaries in row_pairs:
        equal = True
        for index, auxiliary in enumerate(auxiliaries):
            equal = equal and completed[left[index]] == completed[right[index]]
            completed[auxiliary] = equal
    return completed


def verify_lex_semantics(
    clauses: list[tuple[int, ...]], row_pairs: list[tuple[list[int], list[int], list[int]]]
) -> None:
    cursor = 0
    for left, right, auxiliaries in row_pairs:
        gadget = clauses[cursor:cursor + 174]
        cursor += 174
        expected: list[tuple[int, ...]] = [(-left[0], right[0])]
        first = auxiliaries[0]
        expected += [
            (-first, -left[0], right[0]),
            (-first, left[0], -right[0]),
            (left[0], right[0], first),
            (-left[0], -right[0], first),
            (-first, -left[1], right[1]),
        ]
        for bit in range(1, 29):
            previous, current = auxiliaries[bit - 1], auxiliaries[bit]
            expected += [
                (-current, previous),
                (-current, -left[bit], right[bit]),
                (-current, left[bit], -right[bit]),
                (-previous, left[bit], right[bit], current),
                (-previous, -left[bit], -right[bit], current),
                (-current, -left[bit + 1], right[bit + 1]),
            ]
        if gadget != expected:
            raise AssertionError("physical lex comparator differs from cold reconstruction")
        mentioned = set(map(abs, itertools.chain.from_iterable(gadget)))
        if mentioned != set(left + right + auxiliaries):
            raise AssertionError("lex gadget variable support mismatch")
        # Test all 4-bit prefixes with the remaining 26 row bits equal to zero.
        for left_prefix in range(16):
            for right_prefix in range(16):
                primary = {variable: False for variable in left + right}
                for bit in range(4):
                    primary[left[bit]] = bool((left_prefix >> (3 - bit)) & 1)
                    primary[right[bit]] = bool((right_prefix >> (3 - bit)) & 1)
                completed = expected_prefix_values(primary, [(left, right, auxiliaries)])
                accepted = all(clause_true(clause, completed) for clause in gadget)
                direct = tuple(primary[variable] for variable in left) <= tuple(primary[variable] for variable in right)
                if accepted != direct:
                    raise AssertionError("cold lex semantics differs from direct comparison")
    if cursor != len(clauses):
        raise AssertionError("lex gadget partition mismatch")


def main() -> int:
    if len(sys.argv) != 6:
        raise SystemExit(
            "usage: novel42_lex_quotient_audit.py CORPUS CORPUS_REPORT PRODUCTION_REPORT ARTIFACT_DIR OUTPUT"
        )
    corpus, corpus_report, production_report, artifact_dir, output = map(Path, sys.argv[1:])
    if sha256(corpus) != CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")
    retained = json.loads(corpus_report.read_text(encoding="utf-8"))
    production = json.loads(production_report.read_text(encoding="utf-8"))
    if production["strategy_fingerprint"] != "a230b66ef386":
        raise AssertionError("strategy fingerprint mismatch")
    if production["small_gate"]["labelled_graphs_checked"] != 2_097_152:
        raise AssertionError("small coverage gate missing")
    if production["small_gate"]["row_multiplicity_counts"] != {
        "all_distinct": 1_720_320,
        "all_tied": 8_192,
        "one_tied_pair": 368_640,
    }:
        raise AssertionError("small multiplicity census mismatch")

    records = corpus.read_bytes().splitlines()
    sources = [nx.from_graph6_bytes(record) for record in records]
    source = sources[SOURCE_RECORD - 1]
    destroy = destroy_set()
    fixed = sorted(set(range(ORDER)) - set(destroy))
    destroyed = set(destroy)
    edges = [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed or high in destroyed
    ]
    edge_to_variable = {edge: index + 1 for index, edge in enumerate(edges)}
    if len(edges) != 426 or destroy != production["boundary"]["destroy_vertices"]:
        raise AssertionError("cold boundary mapping mismatch")

    cnf_path = artifact_dir / "record-21-lex-source-blocked.cnf"
    variables, clauses = parse_dimacs(cnf_path)
    if sha256(cnf_path) != production["formula"]["cnf_sha256"]:
        raise AssertionError("physical CNF hash mismatch")
    if variables != 745 or len(clauses) != 198_913:
        raise AssertionError("unexpected physical formula dimensions")
    raw = reconstruct_raw(source, destroy, edges)
    if len(raw) != 196_998 or clauses[:len(raw)] != raw:
        raise AssertionError("independent raw Ramsey reconstruction mismatch")
    lex = clauses[len(raw):-1]
    if len(lex) != 1_914:
        raise AssertionError("lex clause count mismatch")

    next_auxiliary = 427
    row_pairs: list[tuple[list[int], list[int], list[int]]] = []
    for left_vertex, right_vertex in zip(destroy, destroy[1:]):
        left = [edge_to_variable[tuple(sorted((left_vertex, core)))] for core in fixed]
        right = [edge_to_variable[tuple(sorted((right_vertex, core)))] for core in fixed]
        auxiliaries = list(range(next_auxiliary, next_auxiliary + 29))
        next_auxiliary += 29
        row_pairs.append((left, right, auxiliaries))
    if next_auxiliary != 746:
        raise AssertionError("auxiliary range mismatch")
    verify_lex_semantics(lex, row_pairs)

    sorted_source = nx.from_graph6_bytes((artifact_dir / "record-21-row-sorted.g6").read_bytes().strip())
    source_primary = {
        variable: sorted_source.has_edge(u, v)
        for variable, (u, v) in enumerate(edges, 1)
    }
    source_values = expected_prefix_values(source_primary, row_pairs)
    if not all(clause_true(clause, source_values) for clause in clauses[:-1]):
        raise AssertionError("cold source positive control fails base formula")
    expected_block = tuple(-variable if source_primary[variable] else variable for variable in range(1, 427))
    if clauses[-1] != expected_block or clause_true(clauses[-1], source_values):
        raise AssertionError("source block mismatch")
    source_rows = [tuple(sorted_source.has_edge(vertex, core) for core in fixed) for vertex in destroy]
    if source_rows != sorted(source_rows) or len(set(source_rows)) != 12:
        raise AssertionError("cold source row-order control failed")

    # Adversarial symmetry control: exchange the first two destroyed labels.
    # The full graph remains an isomorphic Ramsey graph and the frozen core is
    # untouched, so every raw clause must remain true.  Its distinct rows are
    # now out of order, so the lex clauses must reject it.  NetworkX relabels
    # all incident edges simultaneously, including the destroyed-destroyed edge.
    first_destroyed, second_destroyed = destroy[:2]
    swapped_source = nx.relabel_nodes(
        sorted_source,
        {first_destroyed: second_destroyed, second_destroyed: first_destroyed},
        copy=True,
    )
    swapped_primary = {
        variable: swapped_source.has_edge(u, v)
        for variable, (u, v) in enumerate(edges, 1)
    }
    swapped_values = expected_prefix_values(swapped_primary, row_pairs)
    swapped_rows = [tuple(swapped_source.has_edge(vertex, core) for core in fixed) for vertex in destroy]
    if not all(clause_true(clause, swapped_values) for clause in raw):
        raise AssertionError("destroy-label swap unexpectedly violates a raw Ramsey clause")
    if swapped_rows == sorted(swapped_rows) or all(clause_true(clause, swapped_values) for clause in lex):
        raise AssertionError("lex quotient failed to reject an unsorted distinct-row permutation")

    model_entry = production["post_block_model"]
    audited_model: dict[str, object] = {"status": model_entry["status"]}
    if model_entry["status"] == "sat_valid":
        model_path = artifact_dir / "post-block-model.json"
        values = {int(key): bool(value) for key, value in json.loads(model_path.read_text(encoding="ascii")).items()}
        if set(values) != set(range(1, variables + 1)) or not all(clause_true(clause, values) for clause in clauses):
            raise AssertionError("cold total-model DIMACS check failed")
        candidate = nx.from_graph6_bytes((artifact_dir / "post-block-candidate.g6").read_bytes().strip())
        for variable, (u, v) in enumerate(edges, 1):
            if candidate.has_edge(u, v) != values[variable]:
                raise AssertionError("cold primary model-to-graph mismatch")
        for u, v in itertools.combinations(fixed, 2):
            if candidate.has_edge(u, v) != source.has_edge(u, v):
                raise AssertionError("candidate changed a frozen-core edge")
        rows = [tuple(candidate.has_edge(vertex, core) for core in fixed) for vertex in destroy]
        if rows != sorted(rows):
            raise AssertionError("candidate rows are not directly ordered")
        omega = max(map(len, nx.find_cliques(candidate)), default=0)
        alpha = max(map(len, nx.find_cliques(nx.complement(candidate))), default=0)
        if omega >= 5 or alpha >= 5:
            raise AssertionError("NetworkX finds a forbidden five-set")
        target = model_entry["supplied_target"]
        if target is not None:
            record = int(target["record"])
            target_graph = sources[record - 1]
            if target["kind"] == "complement":
                target_graph = nx.complement(target_graph)
            if not nx.is_isomorphic(candidate, target_graph):
                raise AssertionError("NetworkX rejects the reported supplied target")
        elif any(nx.is_isomorphic(candidate, graph) or nx.is_isomorphic(candidate, nx.complement(graph)) for graph in sources):
            raise AssertionError("reported corpus nonmember is isomorphic to a supplied control")
        audited_model.update({
            "physical_clauses_satisfied": len(clauses),
            "graph_clique_number": omega,
            "complement_clique_number": alpha,
            "direct_row_order": True,
            "fixed_core_equal": True,
            "networkx_target_isomorphism": target is not None,
        })

    payload = {
        "schema_version": 1,
        "status": "novel42_lex_quotient_cold_audit_pass",
        "cnf_sha256": sha256(cnf_path),
        "variables": variables,
        "clauses": len(clauses),
        "raw_ramsey_clauses_independently_reconstructed": len(raw),
        "lex_clauses_checked": len(lex),
        "source_control": "passed",
        "adversarial_destroy_swap": {
            "raw_ramsey_clauses_satisfied": len(raw),
            "frozen_core_unchanged": True,
            "direct_rows_unsorted": True,
            "lex_formula_rejected": True,
        },
        "hamming_auxiliaries_present": False,
        "post_block_model": audited_model,
        "corpus_classes": retained["canonical_distinct_classes"],
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
