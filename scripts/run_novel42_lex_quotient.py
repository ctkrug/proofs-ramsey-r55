#!/usr/bin/env python3
"""One-model SAT discriminator for a destroy-label lex quotient.

The source-relative Hamming constraint used in the earlier boundary search is
absent.  The only additional constraints are lexicographic order on the
destroyed vertices' frozen-core adjacency rows.  Exactly one canonical source
primary vector is blocked before one bounded solver call.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time


ORDER = 42
SOURCE_RECORD = 21
DESTROY_COUNT = 12
PRIMARY_VARIABLES = 426
FINGERPRINT = "r55novel42basin2026"
STRATEGY = "a230b66ef386"
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def parse_graph6(record: bytes) -> list[list[bool]]:
    record = record.rstrip(b"\r\n")
    if not record or record[0] != ORDER + 63:
        raise ValueError("expected a short order-42 graph6 record")
    expected = 1 + ((ORDER * (ORDER - 1) // 2 + 5) // 6)
    if len(record) != expected:
        raise ValueError("wrong graph6 record length")
    bits: list[bool] = []
    for byte in record[1:]:
        if not 63 <= byte <= 126:
            raise ValueError("invalid graph6 byte")
        value = byte - 63
        bits.extend(bool((value >> shift) & 1) for shift in range(5, -1, -1))
    adjacency = [[False] * ORDER for _ in range(ORDER)]
    cursor = 0
    for high in range(1, ORDER):
        for low in range(high):
            adjacency[low][high] = adjacency[high][low] = bits[cursor]
            cursor += 1
    if any(bits[cursor:]):
        raise ValueError("nonzero graph6 padding")
    return adjacency


def encode_graph6(adjacency: list[list[bool]]) -> bytes:
    bits = [adjacency[low][high] for high in range(1, ORDER) for low in range(high)]
    bits.extend([False] * ((-len(bits)) % 6))
    body = []
    for offset in range(0, len(bits), 6):
        value = sum(int(bits[offset + bit]) << (5 - bit) for bit in range(6))
        body.append(63 + value)
    return bytes([ORDER + 63, *body]) + b"\n"


def complement(adjacency: list[list[bool]]) -> list[list[bool]]:
    return [[i != j and not adjacency[i][j] for j in range(ORDER)] for i in range(ORDER)]


def stable_destroy() -> list[int]:
    ranked = sorted(
        range(ORDER),
        key=lambda item: hashlib.sha256(
            f"{FINGERPRINT}:destroy:{SOURCE_RECORD - 1}:{item}".encode()
        ).digest(),
    )
    return sorted(ranked[:DESTROY_COUNT])


def variable_edges(destroy: list[int]) -> list[tuple[int, int]]:
    destroyed = set(destroy)
    return [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed or high in destroyed
    ]


def raw_ramsey_clauses(
    adjacency: list[list[bool]], destroy: list[int], edges: list[tuple[int, int]]
) -> tuple[list[tuple[int, ...]], dict[str, int]]:
    destroyed = set(destroy)
    edge_to_variable = {edge: index for index, edge in enumerate(edges, 1)}
    clauses: list[tuple[int, ...]] = []
    clique_count = independent_count = touched = 0
    for vertices in itertools.combinations(range(ORDER), 5):
        if destroyed.isdisjoint(vertices):
            continue
        touched += 1
        variables: list[int] = []
        fixed: list[bool] = []
        for u, v in itertools.combinations(vertices, 2):
            edge = (min(u, v), max(u, v))
            variable = edge_to_variable.get(edge)
            if variable is None:
                fixed.append(adjacency[u][v])
            else:
                variables.append(variable)
        if all(fixed):
            clauses.append(tuple(-variable for variable in variables))
            clique_count += 1
        if not any(fixed):
            clauses.append(tuple(variables))
            independent_count += 1
    if any(not clause for clause in clauses):
        raise AssertionError("the frozen core already contains a forbidden five-set")
    return clauses, {
        "five_sets_touched": touched,
        "clique_clauses": clique_count,
        "independent_clauses": independent_count,
        "ramsey_clauses": len(clauses),
    }


def lex_leq_clauses(left: list[int], right: list[int], auxiliaries: list[int]) -> list[tuple[int, ...]]:
    """Encode left <=lex right with exact prefix-equality auxiliaries.

    auxiliaries[i-1] is true iff the first i bit pairs are equal.  For 30-bit
    rows this uses 29 auxiliaries and 174 clauses.
    """
    if len(left) != len(right) or len(auxiliaries) != len(left) - 1 or len(left) < 2:
        raise ValueError("bad lex comparator dimensions")
    clauses: list[tuple[int, ...]] = [(-left[0], right[0])]
    first = auxiliaries[0]
    clauses.extend([
        (-first, -left[0], right[0]),
        (-first, left[0], -right[0]),
        (left[0], right[0], first),
        (-left[0], -right[0], first),
    ])
    clauses.append((-first, -left[1], right[1]))
    for position in range(1, len(left) - 1):
        previous = auxiliaries[position - 1]
        current = auxiliaries[position]
        x = left[position]
        y = right[position]
        clauses.extend([
            (-current, previous),
            (-current, -x, y),
            (-current, x, -y),
            (-previous, x, y, current),
            (-previous, -x, -y, current),
        ])
        clauses.append((-current, -left[position + 1], right[position + 1]))
    expected = 6 + 6 * (len(left) - 2)
    if len(clauses) != expected:
        raise AssertionError("lex comparator clause accounting failed")
    return clauses


def edge_bit(mask: int, positions: dict[tuple[int, int], int], u: int, v: int) -> int:
    return (mask >> positions[(min(u, v), max(u, v))]) & 1


def exhaustive_small_gate() -> dict[str, object]:
    """Exhaust all labelled graphs on four core plus three destroy vertices."""
    order = 7
    fixed = list(range(4))
    destroyed = list(range(4, 7))
    edges = [(low, high) for high in range(1, order) for low in range(high)]
    positions = {edge: index for index, edge in enumerate(edges)}
    multiplicities = {"all_distinct": 0, "one_tied_pair": 0, "all_tied": 0}
    sorted_outputs = 0
    for mask in range(1 << len(edges)):
        rows = [tuple(edge_bit(mask, positions, vertex, core) for core in fixed) for vertex in destroyed]
        distinct = len(set(rows))
        if distinct == 3:
            multiplicities["all_distinct"] += 1
        elif distinct == 2:
            multiplicities["one_tied_pair"] += 1
        else:
            multiplicities["all_tied"] += 1
        old_order = sorted(destroyed, key=lambda vertex: (rows[vertex - 4], vertex))
        old_for_new = {vertex: vertex for vertex in fixed}
        old_for_new.update({new: old for new, old in zip(destroyed, old_order, strict=True)})
        transformed = 0
        for bit_position, (low, high) in enumerate(edges):
            old_low, old_high = old_for_new[low], old_for_new[high]
            if edge_bit(mask, positions, old_low, old_high):
                transformed |= 1 << bit_position
        new_rows = [
            tuple(edge_bit(transformed, positions, vertex, core) for core in fixed)
            for vertex in destroyed
        ]
        if new_rows != sorted(new_rows):
            raise AssertionError("small graph lost row-sorted coverage")
        if any(
            edge_bit(mask, positions, u, v) != edge_bit(transformed, positions, u, v)
            for u, v in itertools.combinations(fixed, 2)
        ):
            raise AssertionError("destroy permutation changed the frozen core")
        if rows == sorted(rows):
            sorted_outputs += 1
    expected_multiplicities = {
        "all_distinct": 1_720_320,
        "one_tied_pair": 368_640,
        "all_tied": 8_192,
    }
    if multiplicities != expected_multiplicities or sum(multiplicities.values()) != 1 << 21:
        raise AssertionError("small row-multiplicity census mismatch")
    if sorted_outputs != 417_792:
        raise AssertionError("small sorted-representative count mismatch")

    # Independent finite truth table for the exact four-bit comparator gadget.
    ordered_pairs = satisfying_auxiliary_assignments = 0
    for left_value in range(16):
        for right_value in range(16):
            left_bits = tuple(bool((left_value >> (3 - bit)) & 1) for bit in range(4))
            right_bits = tuple(bool((right_value >> (3 - bit)) & 1) for bit in range(4))
            variables = list(range(1, 5))
            right_variables = list(range(5, 9))
            auxiliaries = list(range(9, 12))
            clauses = lex_leq_clauses(variables, right_variables, auxiliaries)
            count = 0
            for auxiliary_mask in range(8):
                values = {
                    **{variable: left_bits[index] for index, variable in enumerate(variables)},
                    **{variable: right_bits[index] for index, variable in enumerate(right_variables)},
                    **{variable: bool((auxiliary_mask >> index) & 1) for index, variable in enumerate(auxiliaries)},
                }
                if all(any(values[abs(lit)] == (lit > 0) for lit in clause) for clause in clauses):
                    count += 1
            directly_ordered = left_bits <= right_bits
            if count != int(directly_ordered):
                raise AssertionError("lex gadget truth table differs from direct comparison")
            ordered_pairs += int(directly_ordered)
            satisfying_auxiliary_assignments += count
    if ordered_pairs != 136 or satisfying_auxiliary_assignments != 136:
        raise AssertionError("lex gadget census mismatch")
    return {
        "labelled_graphs_checked": 1 << 21,
        "row_multiplicity_counts": multiplicities,
        "directly_row_sorted_graphs": sorted_outputs,
        "burnside_s3_orbit_count": 382_976,
        "coverage": "every labelled graph mapped by an explicit destroy permutation to a sorted representative",
        "lex_pair_assignments_checked": 256,
        "directly_ordered_pairs": ordered_pairs,
        "unique_satisfying_prefix_assignments": satisfying_auxiliary_assignments,
    }


def permute_destroyed(
    adjacency: list[list[bool]], destroy: list[int]
) -> tuple[list[list[bool]], list[int], list[tuple[int, ...]]]:
    fixed = sorted(set(range(ORDER)) - set(destroy))
    ranked = sorted(
        (tuple(int(adjacency[vertex][core]) for core in fixed), vertex)
        for vertex in destroy
    )
    old_for_new = {new: old for new, (_, old) in zip(destroy, ranked, strict=True)}
    old_for_new.update({vertex: vertex for vertex in fixed})
    result = [[False] * ORDER for _ in range(ORDER)]
    for high in range(1, ORDER):
        for low in range(high):
            value = adjacency[old_for_new[low]][old_for_new[high]]
            result[low][high] = result[high][low] = value
    rows = [tuple(int(result[vertex][core]) for core in fixed) for vertex in destroy]
    return result, [old_for_new[vertex] for vertex in destroy], rows


def clause_satisfied(clause: tuple[int, ...], values: dict[int, bool]) -> bool:
    return any(values[abs(literal)] == (literal > 0) for literal in clause)


def complete_lex_values(
    primary_values: dict[int, bool], row_pairs: list[tuple[list[int], list[int], list[int]]]
) -> dict[int, bool]:
    values = dict(primary_values)
    for left, right, auxiliaries in row_pairs:
        prefix_equal = True
        for position, auxiliary in enumerate(auxiliaries, 1):
            prefix_equal = prefix_equal and (values[left[position - 1]] == values[right[position - 1]])
            values[auxiliary] = prefix_equal
    return values


def parse_model(stdout: str, variables: int) -> dict[int, bool]:
    result: dict[int, bool] = {}
    for line in stdout.splitlines():
        if line.startswith("v "):
            for text in line[2:].split():
                literal = int(text)
                if literal:
                    result[abs(literal)] = literal > 0
    if any(variable not in result for variable in range(1, variables + 1)):
        raise AssertionError("solver returned an incomplete total model")
    return result


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=180)
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout)


def limit_solver() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024**2, 256 * 1024**2))


def main() -> int:
    if len(sys.argv) != 10:
        raise SystemExit(
            "usage: run_novel42_lex_quotient.py CORPUS CORPUS_REPORT CHECKER_A CHECKER_B_C "
            "OUTPUT_DIR REPORT SOLVE_SECONDS SEED EXPECTED_SOURCE_RECORD"
        )
    corpus, corpus_report, checker_a, checker_b_source, output_dir, report = map(Path, sys.argv[1:7])
    solve_seconds, seed, expected_record = map(int, sys.argv[7:10])
    if solve_seconds != 30 or seed != 1 or expected_record != SOURCE_RECORD:
        raise ValueError("this predeclared experiment requires 30 seconds, seed 1, source record 21")
    if output_dir.exists() or report.exists():
        raise ValueError("output directory or report already exists")
    if digest(corpus) != CORPUS_SHA256:
        raise AssertionError("authenticated corpus hash mismatch")
    retained = json.loads(corpus_report.read_text(encoding="utf-8"))
    if retained.get("canonical_distinct_classes") != 656:
        raise AssertionError("authenticated corpus report mismatch")
    cadical = shutil.which("cadical")
    labelg = shutil.which("nauty-labelg")
    compiler = shutil.which("gcc")
    if not cadical or not labelg or not compiler:
        raise RuntimeError("CaDiCaL, nauty-labelg, and gcc are required")

    started_gate = time.monotonic()
    small_gate = exhaustive_small_gate()
    small_gate["seconds"] = time.monotonic() - started_gate

    records = corpus.read_bytes().splitlines()
    if len(records) != 328:
        raise AssertionError("expected 328 source graph6 records")
    source_graphs = [parse_graph6(record) for record in records]
    source = source_graphs[SOURCE_RECORD - 1]
    destroy = stable_destroy()
    if destroy != [2, 3, 10, 12, 14, 25, 27, 30, 36, 37, 38, 41]:
        raise AssertionError("destroy-set fingerprint drift")
    fixed = sorted(set(range(ORDER)) - set(destroy))
    edges = variable_edges(destroy)
    if len(edges) != PRIMARY_VARIABLES:
        raise AssertionError("boundary primary count mismatch")
    edge_to_variable = {edge: index for index, edge in enumerate(edges, 1)}
    raw_clauses, raw_counts = raw_ramsey_clauses(source, destroy, edges)

    next_variable = PRIMARY_VARIABLES + 1
    row_pairs: list[tuple[list[int], list[int], list[int]]] = []
    lex_clauses: list[tuple[int, ...]] = []
    for left_vertex, right_vertex in zip(destroy, destroy[1:]):
        left = [edge_to_variable[(min(left_vertex, core), max(left_vertex, core))] for core in fixed]
        right = [edge_to_variable[(min(right_vertex, core), max(right_vertex, core))] for core in fixed]
        auxiliaries = list(range(next_variable, next_variable + len(fixed) - 1))
        next_variable += len(auxiliaries)
        row_pairs.append((left, right, auxiliaries))
        lex_clauses.extend(lex_leq_clauses(left, right, auxiliaries))
    variables = next_variable - 1
    if variables != 745 or len(lex_clauses) != 1_914:
        raise AssertionError("production lex formula accounting mismatch")

    sorted_source, old_destroy_order, source_rows = permute_destroyed(source, destroy)
    if source_rows != sorted(source_rows) or len(set(source_rows)) != DESTROY_COUNT:
        raise AssertionError("sorted source is not the expected distinct-row positive control")
    primary_source = {
        variable: sorted_source[u][v]
        for variable, (u, v) in enumerate(edges, 1)
    }
    source_values = complete_lex_values(primary_source, row_pairs)
    base_clauses = raw_clauses + lex_clauses
    if any(not clause_satisfied(clause, source_values) for clause in base_clauses):
        raise AssertionError("row-sorted record 21 does not satisfy regenerated base CNF")
    block = tuple(-variable if primary_source[variable] else variable for variable in range(1, PRIMARY_VARIABLES + 1))
    if clause_satisfied(block, source_values):
        raise AssertionError("canonical source block has wrong polarity")

    output_dir.mkdir(parents=True)
    source_path = output_dir / "record-21-row-sorted.g6"
    source_path.write_bytes(encode_graph6(sorted_source))
    cnf_path = output_dir / "record-21-lex-source-blocked.cnf"
    all_clauses = base_clauses + [block]
    with cnf_path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {variables} {len(all_clauses)}\n")
        for clause in all_clauses:
            stream.write(" ".join(map(str, clause)) + " 0\n")

    with tempfile.TemporaryDirectory(prefix="r55-lex-quotient-") as temporary:
        temp = Path(temporary)
        checker_b = temp / "checker_b"
        subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)],
            check=True,
        )
        controls = source_graphs + [complement(graph) for graph in source_graphs]
        controls_path = temp / "controls.g6"
        controls_path.write_bytes(
            b"".join(record + b"\n" for record in records)
            + b"".join(encode_graph6(graph) for graph in controls[328:])
        )
        canonical_controls_path = temp / "controls.canonical.g6"
        subprocess.run([labelg, "-q", str(controls_path), str(canonical_controls_path)], check=True)
        canonical_controls = set(canonical_controls_path.read_bytes().splitlines())
        if len(canonical_controls) != 656:
            raise AssertionError("canonical control census mismatch")
        canonical_lookup: dict[str, tuple[int, str]] = {}
        for entry in retained["per_record_manifest"]:
            record = int(entry["record"])
            for kind in ("source", "complement"):
                canonical_lookup[entry[f"{kind}_canonical_sha256"]] = (record, kind)

        solver_started = time.monotonic()
        solved = subprocess.run(
            [cadical, "-q", "-t", str(solve_seconds), f"--seed={seed}", str(cnf_path)],
            text=True,
            capture_output=True,
            preexec_fn=limit_solver,
        )
        solver_seconds = time.monotonic() - solver_started
        (output_dir / "cadical.stdout").write_text(solved.stdout, encoding="ascii")
        (output_dir / "cadical.stderr").write_text(solved.stderr, encoding="ascii")
        model_report: dict[str, object] | None = None
        if solved.returncode == 10:
            values = parse_model(solved.stdout, variables)
            if any(not clause_satisfied(clause, values) for clause in all_clauses):
                raise AssertionError("solver model falsifies physical DIMACS")
            candidate = [row[:] for row in source]
            for variable, (u, v) in enumerate(edges, 1):
                candidate[u][v] = candidate[v][u] = values[variable]
            rows = [tuple(int(candidate[vertex][core]) for core in fixed) for vertex in destroy]
            if rows != sorted(rows):
                raise AssertionError("production model violates direct row order")
            if all(values[variable] == primary_source[variable] for variable in range(1, PRIMARY_VARIABLES + 1)):
                raise AssertionError("production model equals the blocked source primary vector")
            candidate_path = output_dir / "post-block-candidate.g6"
            candidate_path.write_bytes(encode_graph6(candidate))
            checked_a = run_json([sys.executable, str(checker_a), "--format", "graph6", "--input", str(candidate_path)])
            checked_b = run_json([str(checker_b), "--format", "graph6", "--input", str(candidate_path)])
            result_a = checked_a["graphs"][0]
            result_b = checked_b["graphs"][0]
            if result_a != result_b or result_a["zero_k5"] or result_a["one_k5"]:
                raise AssertionError("independent full graph checkers reject the production model")
            canonical_path = output_dir / "post-block-candidate.canonical.g6"
            subprocess.run([labelg, "-q", str(candidate_path), str(canonical_path)], check=True)
            canonical_line = canonical_path.read_bytes()
            canonical_hash = hashlib.sha256(canonical_line).hexdigest()
            target = canonical_lookup.get(canonical_hash)
            model_path = output_dir / "post-block-model.json"
            model_path.write_text(
                json.dumps({str(variable): values[variable] for variable in range(1, variables + 1)}, sort_keys=True),
                encoding="ascii",
            )
            model_report = {
                "status": "sat_valid",
                "model_path": str(model_path),
                "model_sha256": digest(model_path),
                "candidate_path": str(candidate_path),
                "candidate_graph6_sha256": digest(candidate_path),
                "canonical_path": str(canonical_path),
                "canonical_sha256": canonical_hash,
                "nauty_canonical_absent_from_supplied_656": target is None,
                "supplied_target": None if target is None else {"record": target[0], "kind": target[1]},
                "rows_distinct": len(set(rows)) == DESTROY_COUNT,
                "direct_row_order": True,
                "physical_dimacs_satisfied": True,
                "python_exact_five_subset_scan": True,
                "c_recursive_bitset_scan": True,
            }
        elif solved.returncode == 20:
            model_report = {
                "status": "unsat_unverified",
                "qualification": "no proof log was requested; this is not a boundary exclusion",
            }
        else:
            model_report = {
                "status": "unknown",
                "qualification": "timeout or solver failure; no mathematical conclusion",
            }

    payload = {
        "schema_version": 1,
        "status": "novel42_lex_quotient_experiment_complete",
        "strategy_fingerprint": STRATEGY,
        "scope": "record-21 frozen order-30 core with S_12 row-order coverage; one canonical source vector blocked",
        "small_gate": small_gate,
        "boundary": {
            "source_record": SOURCE_RECORD,
            "destroy_vertices": destroy,
            "fixed_vertices": len(fixed),
            "variable_edges": len(edges),
            "source_destroy_old_order_at_new_labels": old_destroy_order,
            "source_rows_distinct": True,
        },
        "formula": {
            **raw_counts,
            "lex_adjacent_pairs": len(destroy) - 1,
            "lex_auxiliary_variables": variables - PRIMARY_VARIABLES,
            "lex_clauses": len(lex_clauses),
            "clauses_per_comparator": len(lex_clauses) // (len(destroy) - 1),
            "source_blocks": 1,
            "variables": variables,
            "clauses": len(all_clauses),
            "cnf_path": str(cnf_path),
            "cnf_sha256": digest(cnf_path),
            "hamming_constraint_present": False,
        },
        "source_control": {
            "row_sorted_source_path": str(source_path),
            "row_sorted_source_sha256": digest(source_path),
            "base_clauses_satisfied": len(base_clauses),
            "blocked_primary_vector": True,
        },
        "solver": {
            "name": "CaDiCaL",
            "version": subprocess.run([cadical, "--version"], text=True, capture_output=True, check=True).stdout.strip(),
            "seed": seed,
            "limit_seconds": solve_seconds,
            "memory_limit_bytes": 1024**3,
            "returncode": solved.returncode,
            "seconds": solver_seconds,
        },
        "post_block_model": model_report,
        "claim_limit": "the quotient covers only this fixed-core boundary; one vector block excludes only the row-sorted record-21 primary assignment",
        "prior_art": {
            "nearest_method_ids": [
                "common-edge-subgraph-neighborhoods",
                "random-36-subgraph-extension",
                "known-class-avoidance-bias",
            ],
            "classification": "material_modification",
            "exact_delta": "static S_12 destroyed-label row ordering with exhaustive tied-row controls",
        },
    }
    report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

