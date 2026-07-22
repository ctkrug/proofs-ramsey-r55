#!/usr/bin/env python3
"""Independent cold audit for the post-census residual-SAT packet.

This file deliberately imports no producer module.  It reparses all 656 host
artifacts, reconstructs the record-21 Ramsey and lex clauses, and compares the
physical DIMACS and block ledger byte-semantically.  It then validates a SAT
witness directly or checks an UNSAT proof with drat-trim.  UNKNOWN is reported
as an audited inconclusive stop, never as mathematical evidence.
"""

from __future__ import annotations

import gzip
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

import networkx as nx


N = 42
CORE_SOURCE = 21
REMOVED = [2, 3, 10, 12, 14, 25, 27, 30, 36, 37, 38, 41]
CORE = sorted(set(range(N)) - set(REMOVED))
PRIMARY = 426
VARIABLES = 745
HOSTS = 656
CORPUS_HASH = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
MAX_BLOCKS = 10_000
MAX_HOST_VECTOR_OCCURRENCES = 100_000
PROOF_CHECK_SECONDS = 7200
PROOF_CHECK_MEMORY_BYTES = 2 * 1024**3
PROOF_CHECK_LOG_BYTES = 64 * 1024**2


def sha(path: Path) -> str:
    state = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            state.update(chunk)
    return state.hexdigest()


def line_hash(lines: list[str]) -> str:
    state = hashlib.sha256()
    for line in lines:
        state.update(line.encode("ascii") + b"\n")
    return state.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    try:
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError:
        pass


def proof_checker_limits() -> None:
    for kind, value in (
        (resource.RLIMIT_AS, PROOF_CHECK_MEMORY_BYTES),
        (resource.RLIMIT_FSIZE, PROOF_CHECK_LOG_BYTES),
    ):
        try:
            resource.setrlimit(kind, (value, value))
        except (OSError, ValueError):
            # Darwin does not implement every POSIX limit. The deployed Linux
            # lifecycle also enforces the declared cgroup limits independently.
            pass


def run_drat_check(
    drat_trim: Path,
    cnf: Path,
    proof: Path,
    log: Path,
    timeout_seconds: float = PROOF_CHECK_SECONDS,
) -> tuple[subprocess.CompletedProcess[str] | None, float, bool]:
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as handle:
        try:
            checked = subprocess.run(
                [str(drat_trim), str(cnf), str(proof)],
                text=True,
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=timeout_seconds,
                preexec_fn=proof_checker_limits,
            )
        except subprocess.TimeoutExpired:
            handle.write("\nproof check timed out; audit incomplete\n")
            handle.flush()
            os.fsync(handle.fileno())
            return None, time.monotonic() - started, True
    return checked, time.monotonic() - started, False


def sat_status(absent_from_controls: bool) -> str:
    return "sat_corpus_novel_candidate" if absent_from_controls else "sat_known_control"


def variable_edges() -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    removed = set(REMOVED)
    for upper in range(1, N):
        for lower in range(upper):
            if lower in removed or upper in removed:
                result.append((lower, upper))
    if len(result) != PRIMARY:
        raise AssertionError("independent primary-edge count differs from 426")
    return result


def comparator(a: list[int], b: list[int], equal: list[int]) -> list[tuple[int, ...]]:
    """Fresh derivation: equality prefixes plus one order implication per bit."""
    if len(a) != 30 or len(b) != 30 or len(equal) != 29:
        raise AssertionError("unexpected row comparator size")
    result: list[tuple[int, ...]] = [(-a[0], b[0])]
    result += [
        (-equal[0], -a[0], b[0]),
        (-equal[0], a[0], -b[0]),
        (a[0], b[0], equal[0]),
        (-a[0], -b[0], equal[0]),
    ]
    result.append((-equal[0], -a[1], b[1]))
    for position in range(1, 29):
        previous = equal[position - 1]
        current = equal[position]
        result += [
            (-current, previous),
            (-current, -a[position], b[position]),
            (-current, a[position], -b[position]),
            (-previous, a[position], b[position], current),
            (-previous, -a[position], -b[position], current),
            (-current, -a[position + 1], b[position + 1]),
        ]
    if len(result) != 174:
        raise AssertionError("independent comparator clause count differs from 174")
    return result


def reconstruct(graph: nx.Graph) -> tuple[list[tuple[int, ...]], int]:
    edges = variable_edges()
    lookup = {edge: index for index, edge in enumerate(edges, 1)}
    raw: list[tuple[int, ...]] = []
    removed = set(REMOVED)
    for five in itertools.combinations(range(N), 5):
        if removed.isdisjoint(five):
            continue
        changing: list[int] = []
        constants: list[bool] = []
        for u, v in itertools.combinations(five, 2):
            variable = lookup.get((min(u, v), max(u, v)))
            if variable is None:
                constants.append(graph.has_edge(u, v))
            else:
                changing.append(variable)
        if all(constants):
            raw.append(tuple(-value for value in changing))
        if not any(constants):
            raw.append(tuple(changing))
    if any(not clause for clause in raw):
        raise AssertionError("independent reconstruction finds a forbidden core five-set")

    result = list(raw)
    next_auxiliary = PRIMARY + 1
    for left_vertex, right_vertex in zip(REMOVED, REMOVED[1:]):
        left = [lookup[(min(left_vertex, core), max(left_vertex, core))] for core in CORE]
        right = [lookup[(min(right_vertex, core), max(right_vertex, core))] for core in CORE]
        prefix = list(range(next_auxiliary, next_auxiliary + 29))
        next_auxiliary += 29
        result.extend(comparator(left, right, prefix))
    if next_auxiliary - 1 != VARIABLES:
        raise AssertionError("independent auxiliary range differs from 427..745")
    return result, len(raw)


def expected_host_name(index: int) -> str:
    return f"{'complement' if index >= 328 else 'source'}_record_{index % 328 + 1}"


def independently_enumerate_embeddings(host: nx.Graph, source: nx.Graph) -> list[tuple[int, ...]]:
    pattern = nx.relabel_nodes(
        source.subgraph(CORE).copy(),
        {old: new for new, old in enumerate(CORE)},
        copy=True,
    )
    matcher = nx.algorithms.isomorphism.GraphMatcher(host, pattern)
    embeddings: list[tuple[int, ...]] = []
    for host_to_pattern in matcher.subgraph_isomorphisms_iter():
        if len(host_to_pattern) != len(CORE):
            raise AssertionError("cold VF2 returned a partial core embedding")
        pattern_to_host = {pattern_vertex: host_vertex for host_vertex, pattern_vertex in host_to_pattern.items()}
        embeddings.append(tuple(pattern_to_host[position] for position in range(len(CORE))))
    embeddings.sort()
    if len(embeddings) != len(set(embeddings)):
        raise AssertionError("cold VF2 returned duplicate core embeddings")
    return embeddings


def independently_expand_embedding(
    host: nx.Graph,
    embedding: tuple[int, ...],
) -> tuple[list[int], list[list[int]], list[str]]:
    residual = sorted(set(range(N)) - set(embedding))
    rows = {
        vertex: tuple(host.has_edge(vertex, embedding[position]) for position in range(len(CORE)))
        for vertex in residual
    }
    groups: list[list[int]] = []
    for _row, members in itertools.groupby(
        sorted(residual, key=lambda vertex: (rows[vertex], vertex)),
        key=lambda vertex: rows[vertex],
    ):
        groups.append(list(members))
    multiplicity = math.prod(math.factorial(len(group)) for group in groups)
    if multiplicity > MAX_HOST_VECTOR_OCCURRENCES:
        raise RuntimeError("cold tied-row expansion exceeds the retained per-host cutoff")
    orders: list[list[int]] = []
    vectors: list[str] = []
    for choices in itertools.product(*(itertools.permutations(group) for group in groups)):
        order = [vertex for choice in choices for vertex in choice]
        pullback = {label: embedding[position] for position, label in enumerate(CORE)}
        pullback.update(zip(REMOVED, order, strict=True))
        orders.append(order)
        vectors.append("".join(
            "1" if host.has_edge(pullback[low], pullback[high]) else "0"
            for low, high in variable_edges()
        ))
    if len(orders) != multiplicity or len({tuple(order) for order in orders}) != multiplicity:
        raise AssertionError("cold tied-row expansion is not exact and duplicate-free")
    return [len(group) for group in groups], orders, vectors


def verify_complete_host_coverage(
    host: nx.Graph,
    source: nx.Graph,
    first: dict[str, object],
    row: dict[str, object],
    index: int,
) -> None:
    expected_embeddings = independently_enumerate_embeddings(host, source)
    entries = first.get("embeddings")
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise AssertionError(f"missing complete embedding ledger {index}")
    stored_embeddings = [tuple(entry.get("map_pattern_to_host", [])) for entry in entries]
    if stored_embeddings != expected_embeddings:
        raise AssertionError(f"cold VF2 embedding coverage mismatch {index}")
    mapping_lines = [",".join(map(str, embedding)) for embedding in expected_embeddings]
    if len(expected_embeddings) != row["embedding_count"] or line_hash(mapping_lines) != row["mapping_stream_sha256"]:
        raise AssertionError(f"cold VF2 embedding receipt mismatch {index}")

    host_vectors: set[str] = set()
    occurrences = 0
    for entry_number, (embedding, entry) in enumerate(zip(expected_embeddings, entries, strict=True)):
        group_sizes, orders, vectors = independently_expand_embedding(host, embedding)
        if (
            entry.get("tie_group_sizes") != group_sizes
            or entry.get("tie_multiplicity") != len(orders)
            or entry.get("residual_orders") != orders
            or entry.get("vectors") != vectors
        ):
            raise AssertionError(f"cold exact tied-row expansion mismatch {index}:{entry_number}")
        occurrences += len(orders)
        host_vectors.update(vectors)
        if occurrences > MAX_HOST_VECTOR_OCCURRENCES:
            raise RuntimeError("cold host vector occurrences exceed the retained cutoff")
    exact_vectors = sorted(host_vectors)
    if (
        exact_vectors != first.get("unique_vectors")
        or occurrences != row["vector_occurrences"]
        or len(exact_vectors) != row["unique_vector_count"]
        or line_hash(exact_vectors) != row["vector_stream_sha256"]
    ):
        raise AssertionError(f"cold exact host-vector coverage mismatch {index}")


def census_vectors(
    manifest: Path,
    validation: Path,
    source_graphs: list[nx.Graph] | None = None,
    coverage_checkpoint: Path | None = None,
) -> tuple[list[str], int]:
    receipt = json.loads(validation.read_text(encoding="utf-8"))
    expected_schedule = [
        {"first_host": 0, "last_host": 253, "seconds": 30.0},
        {"first_host": 254, "last_host": 655, "seconds": 60.0},
    ]
    if (
        receipt.get("status") != "valid"
        or receipt.get("hosts") != HOSTS
        or receipt.get("manifest_sha256") != sha(manifest)
        or receipt.get("original_prefix_manifest_sha256")
        != "50946975a8be443f08218377924028e6b4762b0a84fd47f10ecb0125e4cfff95"
        or receipt.get("aggregate_host_gate_schedule") != expected_schedule
    ):
        raise AssertionError("independent audit rejects the census validation binding")
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != HOSTS:
        raise AssertionError("independent audit requires 656 manifest rows")
    coverage_start = 0
    checkpoint_binding: dict[str, object] | None = None
    if coverage_checkpoint is not None:
        if source_graphs is None:
            raise ValueError("coverage checkpoints require source graphs")
        checkpoint_binding = {
            "schema_version": 1,
            "manifest_sha256": sha(manifest),
            "validation_sha256": sha(validation),
            "corpus_sha256": CORPUS_HASH,
            "auditor_sha256": sha(Path(__file__)),
        }
        if coverage_checkpoint.exists():
            checkpoint = json.loads(coverage_checkpoint.read_text(encoding="utf-8"))
            if any(checkpoint.get(key) != value for key, value in checkpoint_binding.items()):
                raise AssertionError("cold coverage checkpoint identity mismatch")
            coverage_start = int(checkpoint.get("next_host", -1))
            if not 0 <= coverage_start <= HOSTS:
                raise AssertionError("cold coverage checkpoint position is invalid")
            expected_status = "complete" if coverage_start == HOSTS else "running"
            if checkpoint.get("status") != expected_status:
                raise AssertionError("cold coverage checkpoint status is inconsistent")

    collected: set[str] = set()
    occurrences = 0
    for index, row in enumerate(rows):
        if row.get("host_index") != index or row.get("case") != expected_host_name(index):
            raise AssertionError(f"noncanonical census row {index}")
        gate = 30.0 if index < 254 else 60.0
        if float(row.get("host_gate_seconds", 0)) != gate or not 0 < float(row.get("host_seconds", 0)) <= gate:
            raise AssertionError(f"invalid host-time receipt {index}")
        artifact = Path(row["artifact"])
        if not artifact.is_absolute():
            artifact = manifest.parent / artifact
        if sha(artifact) != row.get("artifact_sha256"):
            raise AssertionError(f"census artifact digest mismatch {index}")
        with gzip.open(artifact, "rt", encoding="utf-8") as handle:
            packet = json.load(handle)
        first, second = packet.get("bitset"), packet.get("networkx_summary")
        if not isinstance(first, dict) or not isinstance(second, dict):
            raise AssertionError(f"missing dual census records {index}")
        summary_fields = ("embedding_count", "mapping_stream_sha256", "vector_occurrences", "unique_vector_count", "vector_stream_sha256")
        if any(first.get(field) != row.get(field) or second.get(field) != row.get(field) for field in summary_fields):
            raise AssertionError(f"dual census summaries differ {index}")
        vectors = first.get("unique_vectors")
        if not isinstance(vectors, list) or vectors != sorted(set(vectors)):
            raise AssertionError(f"malformed exact vector list {index}")
        if any(not isinstance(vector, str) or len(vector) != PRIMARY or set(vector) - {"0", "1"} for vector in vectors):
            raise AssertionError(f"non-binary or wrong-width vector {index}")
        if len(vectors) != row["unique_vector_count"] or line_hash(vectors) != row["vector_stream_sha256"]:
            raise AssertionError(f"vector receipt mismatch {index}")
        if source_graphs is not None and index >= coverage_start:
            host = source_graphs[index % 328]
            if index >= 328:
                host = nx.complement(host)
            verify_complete_host_coverage(host, source_graphs[20], first, row, index)
            if coverage_checkpoint is not None and checkpoint_binding is not None:
                atomic_json(coverage_checkpoint, {
                    **checkpoint_binding,
                    "status": "complete" if index + 1 == HOSTS else "running",
                    "next_host": index + 1,
                    "updated_unix": time.time(),
                })
        occurrences += int(row["vector_occurrences"])
        collected.update(vectors)
        if len(collected) > MAX_BLOCKS:
            raise RuntimeError("cold block union exceeds the predeclared 10000-vector pilot gate")
    return sorted(collected), occurrences


def vector_clause(bits: str) -> tuple[int, ...]:
    return tuple(-variable if bits[variable - 1] == "1" else variable for variable in range(1, PRIMARY + 1))


def read_dimacs(path: Path) -> tuple[int, list[tuple[int, ...]]]:
    variables = expected = None
    clauses: list[tuple[int, ...]] = []
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        if not line or line.startswith("c"):
            continue
        if line.startswith("p cnf "):
            if variables is not None:
                raise AssertionError("duplicate DIMACS header")
            _, _, variable_text, count_text = line.split()
            variables, expected = int(variable_text), int(count_text)
            continue
        values = [int(text) for text in line.split()]
        if variables is None or not values or values[-1] != 0 or not values[:-1]:
            raise AssertionError(f"malformed DIMACS line {line_number}")
        clause = tuple(values[:-1])
        if any(literal == 0 or abs(literal) > variables for literal in clause):
            raise AssertionError(f"out-of-range DIMACS literal at line {line_number}")
        clauses.append(clause)
    if variables != VARIABLES or expected != len(clauses):
        raise AssertionError("DIMACS header/body mismatch")
    return variables, clauses


def satisfied(clause: tuple[int, ...], assignment: dict[int, bool]) -> bool:
    return any(assignment[abs(literal)] == (literal > 0) for literal in clause)


def max_clique_at_least_five(graph: nx.Graph) -> bool:
    for vertices in itertools.combinations(range(N), 5):
        if all(graph.has_edge(u, v) for u, v in itertools.combinations(vertices, 2)):
            return True
    return False


def main() -> int:
    if len(sys.argv) != 9:
        raise SystemExit(
            "usage: known_class_residual_sat_audit.py CENSUS_MANIFEST CENSUS_VALIDATION CORPUS "
            "CORPUS_REPORT ARTIFACT_DIR PRODUCTION_REPORT DRAT_TRIM OUTPUT"
        )
    manifest, validation, corpus, corpus_report, artifact_dir, production_report, drat_trim, output = map(Path, sys.argv[1:9])
    if output.exists():
        raise ValueError("audit output already exists")
    if sha(corpus) != CORPUS_HASH:
        raise AssertionError("cold audit corpus hash mismatch")
    raw_records = corpus.read_bytes().splitlines()
    if len(raw_records) != 328:
        raise AssertionError("cold audit corpus count mismatch")
    sources = [nx.from_graph6_bytes(record) for record in raw_records]
    retained = json.loads(corpus_report.read_text(encoding="utf-8"))
    if retained.get("canonical_distinct_classes") != HOSTS:
        raise AssertionError("cold audit corpus report mismatch")
    production = json.loads(production_report.read_text(encoding="utf-8"))
    if production.get("status") != "known_class_residual_sat_complete":
        raise AssertionError("production report is not a completed residual-SAT packet")
    recorded_inputs = production.get("inputs", {})
    for key, path in (("census_manifest", manifest), ("census_validation", validation), ("corpus", corpus), ("corpus_report", corpus_report), ("drat_trim", drat_trim)):
        if recorded_inputs.get(key, {}).get("sha256") != sha(path):
            raise AssertionError(f"production input receipt mismatch: {key}")

    coverage_checkpoint = output.with_suffix(output.suffix + ".coverage-checkpoint.json")
    vectors, occurrences = census_vectors(
        manifest, validation, sources, coverage_checkpoint=coverage_checkpoint
    )
    if not vectors:
        raise AssertionError("cold census has no vectors")
    ledger = artifact_dir / "known-primary-vectors.txt.gz"
    with gzip.open(ledger, "rt", encoding="ascii") as handle:
        retained_vectors = handle.read().splitlines()
    if retained_vectors != vectors:
        raise AssertionError("compressed block ledger differs from independent census union")
    census_report = production.get("census", {})
    if (
        census_report.get("block_ledger", {}).get("sha256") != sha(ledger)
        or census_report.get("unique_primary_vectors") != len(vectors)
        or census_report.get("row_sorted_record_21_vector_present") is not True
    ):
        raise AssertionError("production block-ledger accounting or hash differs")
    source = sources[CORE_SOURCE - 1]
    ranked = sorted(REMOVED, key=lambda vertex: (tuple(source.has_edge(vertex, core) for core in CORE), vertex))
    source_pullback = {label: label for label in CORE}
    source_pullback.update(zip(REMOVED, ranked, strict=True))
    source_vector = "".join(
        "1" if source.has_edge(source_pullback[low], source_pullback[high]) else "0"
        for low, high in variable_edges()
    )
    if source_vector not in vectors:
        raise AssertionError("cold block union omits the row-sorted record-21 positive control")
    base, raw_clause_count = reconstruct(source)
    expected_clauses = base + [vector_clause(vector) for vector in vectors]
    cnf = artifact_dir / "record-21-lex-known-classes-blocked.cnf"
    _variable_count, actual_clauses = read_dimacs(cnf)
    if actual_clauses != expected_clauses:
        raise AssertionError("physical DIMACS differs from independent raw+lex+block reconstruction")
    formula_report = production.get("formula", {})
    if (
        formula_report.get("cnf", {}).get("sha256") != sha(cnf)
        or formula_report.get("base_clauses") != len(base)
        or formula_report.get("class_blocks") != len(vectors)
        or formula_report.get("total_clauses") != len(actual_clauses)
    ):
        raise AssertionError("production formula accounting or hash differs")
    if formula_report.get("hamming_constraint_present") is not False:
        raise AssertionError("production report does not exclude a Hamming restriction")

    solver = production.get("solver", {})
    solver_stdout = artifact_dir / "cadical.stdout"
    solver_stderr = artifact_dir / "cadical.stderr"
    if (
        solver.get("seed") != 1
        or not 1 <= int(solver.get("wall_limit_seconds", 0)) <= 3600
        or not 256 * 1024**2 <= int(solver.get("proof_file_limit_bytes", 0)) <= 6 * 1024**3
        or solver.get("root_disk_reserve_bytes") != 8 * 1024**3
        or solver.get("nonproof_headroom_bytes") != 512 * 1024**2
        or solver.get("stdout", {}).get("sha256") != sha(solver_stdout)
        or solver.get("stderr", {}).get("sha256") != sha(solver_stderr)
    ):
        raise AssertionError("solver limit, seed, or log receipt mismatch")
    solver_text = solver_stdout.read_text(encoding="ascii")
    solver_returncode = solver.get("returncode")

    result = production.get("result", {})
    status = result.get("status")
    audited: dict[str, object]
    if status in ("sat_corpus_novel_candidate", "sat_known_control"):
        if solver_returncode != 10 or "s SATISFIABLE" not in solver_text:
            raise AssertionError("SAT report disagrees with preserved solver verdict")
        model_path = artifact_dir / "model.json"
        candidate_path = artifact_dir / "candidate.g6"
        retained_canonical = artifact_dir / "candidate.canonical.g6"
        if (
            result.get("model", {}).get("sha256") != sha(model_path)
            or result.get("candidate", {}).get("sha256") != sha(candidate_path)
            or result.get("canonical_candidate", {}).get("sha256") != sha(retained_canonical)
            or result.get("physical_dimacs_satisfied") is not True
            or result.get("direct_row_order") is not True
            or result.get("python_and_c_full_graph_checks_agree") is not True
        ):
            raise AssertionError("SAT artifact hashes or production checker receipts differ")
        assignment = {int(key): bool(value) for key, value in json.loads(model_path.read_text(encoding="ascii")).items()}
        if set(assignment) != set(range(1, VARIABLES + 1)) or not all(satisfied(clause, assignment) for clause in actual_clauses):
            raise AssertionError("cold SAT model does not satisfy the physical DIMACS")
        candidate = nx.from_graph6_bytes(candidate_path.read_bytes().strip())
        for variable, (u, v) in enumerate(variable_edges(), 1):
            if candidate.has_edge(u, v) != assignment[variable]:
                raise AssertionError("cold primary model-to-graph mapping mismatch")
        for u, v in itertools.combinations(CORE, 2):
            if candidate.has_edge(u, v) != source.has_edge(u, v):
                raise AssertionError("SAT candidate changes the frozen core")
        rows = [tuple(candidate.has_edge(vertex, core) for core in CORE) for vertex in REMOVED]
        if rows != sorted(rows):
            raise AssertionError("cold SAT candidate violates row-lex order")
        if max_clique_at_least_five(candidate) or max_clique_at_least_five(nx.complement(candidate)):
            raise AssertionError("cold exhaustive scan finds a forbidden five-set")
        labelg = shutil.which("nauty-labelg")
        if labelg is None:
            raise RuntimeError("nauty-labelg is required for cold SAT classification")
        import tempfile
        with tempfile.TemporaryDirectory(prefix="r55-residual-audit-") as temporary_name:
            temporary = Path(temporary_name)
            controls = temporary / "controls.g6"
            controls.write_bytes(
                b"".join(record + b"\n" for record in raw_records)
                + b"".join(nx.to_graph6_bytes(nx.complement(graph), header=False) for graph in sources)
            )
            canonical_controls = temporary / "controls.canonical.g6"
            subprocess.run([labelg, "-q", str(controls), str(canonical_controls)], check=True)
            control_set = set(canonical_controls.read_bytes().splitlines())
            if len(control_set) != HOSTS:
                raise AssertionError("cold nauty controls are not 656 distinct classes")
            canonical_candidate = temporary / "candidate.canonical.g6"
            subprocess.run([labelg, "-q", str(candidate_path), str(canonical_candidate)], check=True)
            if canonical_candidate.read_bytes() != retained_canonical.read_bytes():
                raise AssertionError("cold nauty canonical bytes differ from the retained artifact")
            absent = canonical_candidate.read_bytes().strip() not in control_set
        if absent != bool(result.get("nauty_canonical_absent_from_supplied_656")):
            raise AssertionError("cold nauty classification differs from production")
        if status != sat_status(absent):
            raise AssertionError("SAT terminal status disagrees with cold corpus classification")
        audited = {
            "status": f"{sat_status(absent)}_cold_audit",
            "physical_clauses_satisfied": len(actual_clauses),
            "frozen_core_equal": True,
            "direct_row_order": True,
            "exhaustive_python_five_set_scan": True,
            "nauty_canonical_absent_from_supplied_656": absent,
            "claim_limit": (
                "candidate only; corpus nonmembership is not a literature novelty result"
                if absent else
                "known supplied-corpus control; the discriminator produced no candidate contribution"
            ),
        }
    elif status == "unsat_verified":
        if solver_returncode != 20 or "s UNSATISFIABLE" not in solver_text:
            raise AssertionError("UNSAT report disagrees with preserved solver verdict")
        proof = artifact_dir / "cadical.drat"
        production_checker_log = artifact_dir / "drat-trim.log"
        if result.get("proof", {}).get("sha256") != sha(proof):
            raise AssertionError("production proof hash differs from preserved proof")
        if result.get("proof_check", {}).get("sha256") != sha(production_checker_log):
            raise AssertionError("production proof-check log hash differs")
        check_index = 0
        while True:
            cold_checker_log = output.with_suffix(output.suffix + f".drat-trim-{check_index:04d}.log")
            if not cold_checker_log.exists():
                break
            check_index += 1
        checked, _check_seconds, timed_out = run_drat_check(
            drat_trim, cnf, proof, cold_checker_log
        )
        if timed_out:
            raise RuntimeError(
                f"cold DRAT check timed out; audit incomplete; partial log preserved at {cold_checker_log}"
            )
        checker_text = cold_checker_log.read_text(encoding="utf-8")
        if checked is None or checked.returncode != 0 or "s VERIFIED" not in checker_text:
            raise AssertionError("cold drat-trim run rejects the UNSAT proof")
        audited = {
            "status": "unsat_proof_cold_audit",
            "proof_sha256": sha(proof),
            "drat_trim_verdict": "VERIFIED",
            "proof_check_log_sha256": sha(cold_checker_log),
            "proof_check_limits": {
                "wall_seconds": PROOF_CHECK_SECONDS,
                "memory_bytes": PROOF_CHECK_MEMORY_BYTES,
                "log_bytes": PROOF_CHECK_LOG_BYTES,
            },
            "claim_limit": "classification only within the record-21 frozen-core S_12 quotient and exact complete-census block set",
        }
    elif status == "unknown":
        proof = artifact_dir / "cadical.drat"
        if result.get("proof_bytes_preserved") != proof.stat().st_size:
            raise AssertionError("UNKNOWN partial-proof size receipt differs")
        if result.get("reason") in ("proof_check_timeout", "proof_check_failed"):
            proof_check = artifact_dir / "drat-trim.log"
            if (
                solver_returncode != 20
                or "s UNSATISFIABLE" not in solver_text
                or result.get("proof", {}).get("sha256") != sha(proof)
                or result.get("proof_check", {}).get("sha256") != sha(proof_check)
            ):
                raise AssertionError("proof-check-incomplete UNKNOWN receipts differ")
            audited = {
                "status": "unknown_proof_check_incomplete_audit",
                "solver_returncode": solver_returncode,
                "reason": result.get("reason"),
                "claim_limit": "solver UNSAT verdict is not evidence until its proof is checked",
            }
        else:
            if solver_returncode in (10, 20) or "s SATISFIABLE" in solver_text or "s UNSATISFIABLE" in solver_text:
                raise AssertionError("UNKNOWN report suppresses a recognized solver verdict")
            audited = {
                "status": "unknown_inconclusive_audit",
                "solver_returncode": result.get("returncode"),
                "claim_limit": "no mathematical conclusion",
            }
    else:
        raise AssertionError("unrecognized production result status")

    payload = {
        "schema_version": 1,
        "status": "known_class_residual_sat_cold_audit_pass",
        "production_report_sha256": sha(production_report),
        "census_manifest_sha256": sha(manifest),
        "hosts_checked": HOSTS,
        "vector_occurrences": occurrences,
        "unique_vectors": len(vectors),
        "raw_ramsey_clauses_independently_reconstructed": raw_clause_count,
        "lex_clauses_independently_reconstructed": len(base) - raw_clause_count,
        "class_blocks_independently_reconstructed": len(vectors),
        "physical_cnf_sha256": sha(cnf),
        "coverage_checkpoint_sha256": sha(coverage_checkpoint),
        "result": audited,
        "independence": "No producer import; census artifacts, graph formula, lex gadgets, vector blocks, physical DIMACS, and result evidence were reconstructed directly.",
        "claim_limit": "This audit establishes packet consistency only within the declared fixed-core quotient.",
    }
    atomic_json(output, payload)
    print(json.dumps({"status": payload["status"], "result": audited["status"], "output_sha256": sha(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
