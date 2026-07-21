#!/usr/bin/env python3
"""Deterministic exact-boundary repair discriminator for Ramsey(5,5,42).

The induced graph outside a declared destroy set is frozen.  Edges meeting the
destroy set are SAT variables.  Every five-set is constrained against being a
clique or independent set, and a sequential cardinality constraint forces a
declared minimum Hamming distance from the authenticated source graph.

This is a discovery harness, not an exhaustive classifier.  It stops at the
first dual-checked graph canonically outside the supplied 656 controls.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time


ORDER = 42
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
FINGERPRINT = "r55novel42basin2026"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def parse_graph6(record: bytes) -> list[list[bool]]:
    record = record.rstrip(b"\r\n")
    if not record or record[0] != ORDER + 63:
        raise ValueError("expected short order-42 graph6 record")
    needed = 1 + ((ORDER * (ORDER - 1) // 2 + 5) // 6)
    if len(record) != needed:
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


def stable_sample(label: str, population: list[int], count: int) -> list[int]:
    ranked = sorted(population, key=lambda item: hashlib.sha256(f"{FINGERPRINT}:{label}:{item}".encode()).digest())
    return sorted(ranked[:count])


def emit_at_most(stream, literals: list[int], bound: int, next_variable: int) -> tuple[int, int]:
    """Sinz sequential at-most-k encoding, independently specialized here."""
    number = len(literals)
    if not 0 < bound < number:
        raise ValueError("this harness requires a nontrivial cardinality bound")
    start = next_variable

    def aux(i: int, j: int) -> int:
        return start + (i - 1) * bound + (j - 1)

    clauses: list[tuple[int, ...]] = []
    clauses.append((-literals[0], aux(1, 1)))
    for j in range(2, bound + 1):
        clauses.append((-aux(1, j),))
    for i in range(2, number):
        clauses.append((-literals[i - 1], aux(i, 1)))
        clauses.append((-aux(i - 1, 1), aux(i, 1)))
        for j in range(2, bound + 1):
            clauses.append((-literals[i - 1], -aux(i - 1, j - 1), aux(i, j)))
            clauses.append((-aux(i - 1, j), aux(i, j)))
    for i in range(2, number + 1):
        clauses.append((-literals[i - 1], -aux(i - 1, bound)))
    for clause in clauses:
        stream.write(" ".join(map(str, clause)) + " 0\n")
    return next_variable + (number - 1) * bound, len(clauses)


def build_cnf(
    adjacency: list[list[bool]], destroy: list[int], minimum_distance: int, path: Path
) -> tuple[list[tuple[int, int]], dict[str, object]]:
    destroyed = set(destroy)
    variable_edges = [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed or high in destroyed
    ]
    edge_to_var = {edge: index for index, edge in enumerate(variable_edges, 1)}
    clauses: list[tuple[int, ...]] = []
    five_sets_touched = 0
    clique_clauses = 0
    independent_clauses = 0
    for vertices in itertools.combinations(range(ORDER), 5):
        if destroyed.isdisjoint(vertices):
            continue
        five_sets_touched += 1
        variables: list[tuple[int, bool]] = []
        fixed: list[bool] = []
        for u, v in itertools.combinations(vertices, 2):
            edge = (min(u, v), max(u, v))
            variable = edge_to_var.get(edge)
            if variable is None:
                fixed.append(adjacency[u][v])
            else:
                variables.append((variable, adjacency[u][v]))
        if all(fixed):
            clauses.append(tuple(-variable for variable, _ in variables))
            clique_clauses += 1
        if not any(fixed):
            clauses.append(tuple(variable for variable, _ in variables))
            independent_clauses += 1
    if any(not clause for clause in clauses):
        raise AssertionError("frozen boundary already contains a forbidden five-set")

    # A literal is true exactly when the corresponding boundary edge matches
    # its source value.  At most m-d matches forces distance at least d.
    matches = [var if adjacency[u][v] else -var for var, (u, v) in enumerate(variable_edges, 1)]
    match_bound = len(matches) - minimum_distance
    cardinality_aux = (len(matches) - 1) * match_bound
    cardinality_clauses = 2 * match_bound * len(matches) - 3 * match_bound + len(matches) - 1
    variables = len(variable_edges) + cardinality_aux
    total_clauses = len(clauses) + cardinality_clauses
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {variables} {total_clauses}\n")
        for clause in clauses:
            stream.write(" ".join(map(str, clause)) + " 0\n")
        next_variable, emitted = emit_at_most(stream, matches, match_bound, len(variable_edges) + 1)
    if next_variable != variables + 1 or emitted != cardinality_clauses:
        raise AssertionError("cardinality accounting mismatch")
    return variable_edges, {
        "destroy_vertices": destroy,
        "variable_edges": len(variable_edges),
        "minimum_hamming_distance": minimum_distance,
        "fixed_vertices": ORDER - len(destroy),
        "five_sets_touched": five_sets_touched,
        "ramsey_clauses": len(clauses),
        "clique_clauses": clique_clauses,
        "independent_clauses": independent_clauses,
        "cardinality_auxiliary_variables": cardinality_aux,
        "cardinality_clauses": cardinality_clauses,
        "variables": variables,
        "clauses": total_clauses,
    }


def parse_model(stdout: str, primary: int) -> list[bool]:
    values: dict[int, bool] = {}
    for line in stdout.splitlines():
        if line.startswith("v "):
            for literal_text in line[2:].split():
                literal = int(literal_text)
                if literal:
                    values[abs(literal)] = literal > 0
    if any(variable not in values for variable in range(1, primary + 1)):
        raise AssertionError("incomplete SAT witness")
    return [values[variable] for variable in range(1, primary + 1)]


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=180)
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout)


def degrees(adjacency: list[list[bool]]) -> list[int]:
    return [sum(row) for row in adjacency]


def histogram_key(adjacency: list[list[bool]]) -> tuple[int, ...]:
    return tuple(sorted(degrees(adjacency)))


def limit_solver() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024 * 1024, 256 * 1024 * 1024))


def main() -> int:
    if len(sys.argv) != 8:
        raise SystemExit(
            "usage: run_novel42_boundary_repair.py CORPUS CORPUS_REPORT CHECKER_A CHECKER_B_C OUTPUT_DIR REPORT TRIAL_SECONDS"
        )
    corpus, corpus_report, checker_a, checker_b_source, output_dir, report = map(Path, sys.argv[1:7])
    trial_seconds = int(sys.argv[7])
    if output_dir.exists() or report.exists():
        raise ValueError("output directory or report already exists")
    if digest(corpus) != CORPUS_SHA256:
        raise AssertionError("authenticated corpus hash mismatch")
    retained = json.loads(corpus_report.read_text(encoding="utf-8"))
    if retained.get("canonical_distinct_classes") != 656 or retained.get("forbidden_sets") != {"one_k5": 0, "zero_k5": 0}:
        raise AssertionError("retained corpus gate mismatch")
    cadical = shutil.which("cadical")
    labelg = shutil.which("nauty-labelg")
    compiler = shutil.which("gcc")
    if not cadical or not labelg or not compiler:
        raise RuntimeError("CaDiCaL, nauty-labelg, and gcc are required")

    source_records = corpus.read_bytes().splitlines()
    if len(source_records) != 328:
        raise AssertionError("expected 328 source-side records")
    source_graphs = [parse_graph6(record) for record in source_records]
    all_controls = source_graphs + [complement(graph) for graph in source_graphs]
    control_histograms = Counter(histogram_key(graph) for graph in all_controls)
    output_dir.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="r55-novel42-") as temporary:
        temp = Path(temporary)
        checker_b = temp / "checker_b"
        subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)],
            check=True,
        )
        controls_g6 = temp / "controls.g6"
        controls_g6.write_bytes(
            b"".join(record + b"\n" for record in source_records)
            + b"".join(encode_graph6(graph) for graph in all_controls[328:])
        )
        canonical_controls_path = temp / "controls.canonical.g6"
        subprocess.run([labelg, "-q", str(controls_g6), str(canonical_controls_path)], check=True)
        canonical_controls = set(canonical_controls_path.read_bytes().splitlines())
        if len(canonical_controls) != 656:
            raise AssertionError("cold canonical control set does not have 656 classes")

        # Source-side only: complement partners never occur in the trial set.
        # The record list and destroy sets are determined only by the stable
        # strategy fingerprint, before any solver result is observed.
        record_indices = stable_sample("records", list(range(328)), 8)
        trials: list[dict[str, object]] = []
        witness_metadata: dict[str, object] | None = None
        for position, record_index in enumerate(record_indices):
            destroy = stable_sample(f"destroy:{record_index}", list(range(ORDER)), 12)
            minimum_distance = 60
            trial_dir = output_dir / f"trial-{position + 1:02d}-record-{record_index + 1:04d}"
            trial_dir.mkdir()
            cnf = trial_dir / "repair.cnf"
            variable_edges, generation = build_cnf(source_graphs[record_index], destroy, minimum_distance, cnf)
            generation["cnf_sha256"] = digest(cnf)
            started = time.monotonic()
            solved = subprocess.run(
                [cadical, "-q", "-t", str(trial_seconds), f"--seed={position + 1}", str(cnf)],
                text=True,
                capture_output=True,
                preexec_fn=limit_solver,
            )
            elapsed = time.monotonic() - started
            (trial_dir / "cadical.stdout").write_text(solved.stdout, encoding="ascii")
            (trial_dir / "cadical.stderr").write_text(solved.stderr, encoding="ascii")
            trial: dict[str, object] = {
                "trial": position + 1,
                "source_record": record_index + 1,
                "source_graph6_sha256": hashlib.sha256(source_records[record_index] + b"\n").hexdigest(),
                "generation": generation,
                "solver_seed": position + 1,
                "solver_returncode": solved.returncode,
                "solver_seconds": elapsed,
            }
            if solved.returncode == 10:
                bits = parse_model(solved.stdout, len(variable_edges))
                candidate = [row[:] for row in source_graphs[record_index]]
                for bit, (u, v) in zip(bits, variable_edges, strict=True):
                    candidate[u][v] = candidate[v][u] = bit
                actual_distance = sum(
                    candidate[u][v] != source_graphs[record_index][u][v] for u, v in variable_edges
                )
                fixed_consistent = all(
                    candidate[u][v] == source_graphs[record_index][u][v]
                    for u, v in itertools.combinations(range(ORDER), 2)
                    if u not in destroy and v not in destroy
                )
                if actual_distance < minimum_distance or not fixed_consistent:
                    raise AssertionError("decoded boundary model violates declared repair scope")
                candidate_path = trial_dir / "candidate.g6"
                candidate_path.write_bytes(encode_graph6(candidate))
                payload_a = run_json([sys.executable, str(checker_a), "--format", "graph6", "--input", str(candidate_path)])
                payload_b = run_json([str(checker_b), "--format", "graph6", "--input", str(candidate_path)])
                checked_a = payload_a["graphs"][0]
                checked_b = payload_b["graphs"][0]
                if checked_a != checked_b:
                    raise AssertionError("independent full graph checkers disagree")
                valid = not checked_a["zero_k5"] and not checked_a["one_k5"]
                if not valid:
                    raise AssertionError("SAT model failed full five-set scan")
                canonical_path = trial_dir / "candidate.canonical.g6"
                subprocess.run([labelg, "-q", str(candidate_path), str(canonical_path)], check=True)
                canonical = canonical_path.read_bytes().strip()
                canonical_novel = canonical not in canonical_controls
                key = histogram_key(candidate)
                histogram_novel = key not in control_histograms
                trial.update({
                    "status": "sat_valid",
                    "actual_boundary_hamming_distance": actual_distance,
                    "fixed_outside_boundary": fixed_consistent,
                    "candidate_graph6_sha256": digest(candidate_path),
                    "candidate_canonical_sha256": hashlib.sha256(canonical + b"\n").hexdigest(),
                    "degree_histogram": dict(sorted(Counter(degrees(candidate)).items())),
                    "degree_multiset_absent_from_controls": histogram_novel,
                    "nauty_canonical_absent_from_controls": canonical_novel,
                    "python_direct_five_subset_scan": True,
                    "c_recursive_bitset_scan": True,
                })
                if canonical_novel:
                    witness_metadata = {
                        "trial": position + 1,
                        "source_record": record_index + 1,
                        "candidate_path": str(candidate_path.relative_to(output_dir.parent)),
                        "candidate_canonical_path": str(canonical_path.relative_to(output_dir.parent)),
                        "graph6_sha256": digest(candidate_path),
                        "canonical_sha256": hashlib.sha256(canonical + b"\n").hexdigest(),
                        "actual_boundary_hamming_distance": actual_distance,
                        "degree_multiset_absent_from_controls": histogram_novel,
                        "nauty_canonical_absent_from_controls": True,
                    }
                    trials.append(trial)
                    break
            elif solved.returncode == 20:
                trial.update({
                    "status": "unsat_unverified",
                    "qualification": "no proof log was requested; this leaf is not an exclusion certificate",
                })
            else:
                trial.update({"status": "unknown", "qualification": "timeout or solver failure; no mathematical claim"})
            trials.append(trial)

    payload = {
        "schema_version": 1,
        "status": "novel42_boundary_repair_complete",
        "scope": "predeclared source-side controls; 12-vertex exact boundary repairs at distance at least 60; stops at first supplied-corpus-novel valid model",
        "claim_limit": "novel means absent from the supplied 656 only, not historically new and not outside an exhaustive census",
        "hypothesis": "at least one predeclared 12-vertex boundary admits a valid Ramsey(5,5,42) repair at distance at least 60 outside all supplied 656 canonical classes",
        "corpus": {"path": str(corpus), "sha256": digest(corpus), "classes": len(canonical_controls)},
        "leakage_control": {
            "trial_side": "328 source records only",
            "complement_partners_used_as_trials": False,
            "selection_rule": f"SHA-256 ranking under fingerprint {FINGERPRINT}",
            "predeclared_record_indices_one_based": [index + 1 for index in record_indices],
            "adaptive_trial_selection": False,
        },
        "trials": trials,
        "witness": witness_metadata,
        "result": "supplied_corpus_novel_valid_order42" if witness_metadata else "no_novel_witness_in_executed_trials",
        "tool_versions": {
            "python": sys.version.split()[0],
            "gcc": subprocess.run([compiler, "--version"], text=True, capture_output=True).stdout.splitlines()[0],
            "cadical": subprocess.run([cadical, "--version"], text=True, capture_output=True).stdout.strip(),
            "nauty_labelg": subprocess.run([labelg], text=True, capture_output=True).stderr.splitlines()[1].strip(),
        },
        "independence": {
            "producer": str(Path(__file__).resolve()),
            "checker_a": {"path": str(checker_a), "sha256": digest(checker_a), "method": "direct itertools five-subset scan"},
            "checker_b": {"path": str(checker_b_source), "sha256": digest(checker_b_source), "method": "C recursive bitset clique scans in graph and complement"},
            "novelty_a": "nauty canonical graph6 nonmembership",
            "novelty_b": "degree multiset nonmembership when reported true",
        },
    }
    report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "result": payload["result"],
        "trials_executed": len(trials),
        "witness": witness_metadata,
        "report": str(report),
        "report_sha256": digest(report),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
