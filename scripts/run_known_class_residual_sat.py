#!/usr/bin/env python3
"""Bounded residual SAT discriminator after the complete v2 embedding census.

This producer fails closed unless a separately validated 656-host census is
present.  It rebuilds the record-21 frozen-core S_12 row-lex quotient, blocks
every exact primary vector retained by that census, and performs exactly one
bounded seed-1 CaDiCaL solve.  SAT candidates are checked by two independent
full-graph checkers and classified with nauty.  UNSAT is accepted only after
the emitted DRAT proof passes drat-trim.  UNKNOWN has no mathematical force.
"""

from __future__ import annotations

import gzip
import hashlib
import itertools
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time


ORDER = 42
SOURCE_RECORD = 21
DESTROY = [2, 3, 10, 12, 14, 25, 27, 30, 36, 37, 38, 41]
FIXED = sorted(set(range(ORDER)) - set(DESTROY))
PRIMARY_VARIABLES = 426
TOTAL_VARIABLES = 745
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
EXPECTED_HOSTS = 656
PREFIX_HOSTS = 254
PREFIX_MANIFEST_SHA256 = "50946975a8be443f08218377924028e6b4762b0a84fd47f10ecb0125e4cfff95"
HOST_GATE_SCHEDULE = [
    {"first_host": 0, "last_host": 253, "seconds": 30.0},
    {"first_host": 254, "last_host": 655, "seconds": 60.0},
]
MAX_SOLVE_SECONDS = 3600
MAX_UNIQUE_VECTORS = 10_000
MAX_PROOF_FILE_BYTES = 6 * 1024**3
ROOT_DISK_RESERVE_BYTES = 8 * 1024**3
NONPROOF_HEADROOM_BYTES = 512 * 1024**2
PROOF_CHECK_SECONDS = 7200
PROOF_CHECK_MEMORY_BYTES = 2 * 1024**3
PROOF_CHECK_LOG_BYTES = 64 * 1024**2


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def stream_digest(lines: list[str]) -> str:
    return hashlib.sha256(b"".join((line + "\n").encode("ascii") for line in lines)).hexdigest()


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
    return [[u != v and not adjacency[u][v] for v in range(ORDER)] for u in range(ORDER)]


def boundary_edges() -> list[tuple[int, int]]:
    destroyed = set(DESTROY)
    edges = [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed or high in destroyed
    ]
    if len(edges) != PRIMARY_VARIABLES:
        raise AssertionError("boundary edge accounting drift")
    return edges


def ramsey_clauses(source: list[list[bool]], edges: list[tuple[int, int]]) -> list[tuple[int, ...]]:
    edge_to_variable = {edge: index for index, edge in enumerate(edges, 1)}
    clauses: list[tuple[int, ...]] = []
    for vertices in itertools.combinations(range(ORDER), 5):
        if set(vertices).isdisjoint(DESTROY):
            continue
        variables: list[int] = []
        fixed: list[bool] = []
        for u, v in itertools.combinations(vertices, 2):
            variable = edge_to_variable.get((min(u, v), max(u, v)))
            if variable is None:
                fixed.append(source[u][v])
            else:
                variables.append(variable)
        if all(fixed):
            clauses.append(tuple(-variable for variable in variables))
        if not any(fixed):
            clauses.append(tuple(variables))
    if any(not clause for clause in clauses):
        raise AssertionError("the frozen core contains a forbidden five-set")
    return clauses


def lex_leq_clauses(left: list[int], right: list[int], auxiliaries: list[int]) -> list[tuple[int, ...]]:
    if len(left) != len(right) or len(auxiliaries) != len(left) - 1 or len(left) < 2:
        raise ValueError("bad lex comparator dimensions")
    clauses: list[tuple[int, ...]] = [(-left[0], right[0])]
    first = auxiliaries[0]
    clauses.extend([
        (-first, -left[0], right[0]),
        (-first, left[0], -right[0]),
        (left[0], right[0], first),
        (-left[0], -right[0], first),
        (-first, -left[1], right[1]),
    ])
    for position in range(1, len(left) - 1):
        previous = auxiliaries[position - 1]
        current = auxiliaries[position]
        x, y = left[position], right[position]
        clauses.extend([
            (-current, previous),
            (-current, -x, y),
            (-current, x, -y),
            (-previous, x, y, current),
            (-previous, -x, -y, current),
            (-current, -left[position + 1], right[position + 1]),
        ])
    return clauses


def build_formula(source: list[list[bool]]) -> tuple[list[tuple[int, ...]], list[tuple[list[int], list[int], list[int]]]]:
    edges = boundary_edges()
    edge_to_variable = {edge: index for index, edge in enumerate(edges, 1)}
    clauses = ramsey_clauses(source, edges)
    next_variable = PRIMARY_VARIABLES + 1
    row_pairs: list[tuple[list[int], list[int], list[int]]] = []
    for left_vertex, right_vertex in zip(DESTROY, DESTROY[1:]):
        left = [edge_to_variable[(min(left_vertex, core), max(left_vertex, core))] for core in FIXED]
        right = [edge_to_variable[(min(right_vertex, core), max(right_vertex, core))] for core in FIXED]
        auxiliaries = list(range(next_variable, next_variable + len(FIXED) - 1))
        next_variable += len(auxiliaries)
        row_pairs.append((left, right, auxiliaries))
        clauses.extend(lex_leq_clauses(left, right, auxiliaries))
    if next_variable - 1 != TOTAL_VARIABLES:
        raise AssertionError("lex auxiliary accounting drift")
    return clauses, row_pairs


def vector_block(vector: str) -> tuple[int, ...]:
    if len(vector) != PRIMARY_VARIABLES or set(vector) - {"0", "1"}:
        raise ValueError("census vector is not an exact 426-bit binary row-lex vector")
    return tuple(-index if bit == "1" else index for index, bit in enumerate(vector, 1))


def row_sorted_source_vector(source: list[list[bool]]) -> str:
    ranked = sorted(
        DESTROY,
        key=lambda vertex: (tuple(source[vertex][core] for core in FIXED), vertex),
    )
    old_for_label = {label: label for label in FIXED}
    old_for_label.update(zip(DESTROY, ranked, strict=True))
    return "".join(
        "1" if source[old_for_label[low]][old_for_label[high]] else "0"
        for low, high in boundary_edges()
    )


def expected_case(index: int) -> str:
    kind = "complement" if index >= 328 else "source"
    return f"{kind}_record_{index % 328 + 1}"


def expected_host_gate(index: int) -> float:
    return 30.0 if index < PREFIX_HOSTS else 60.0


def load_validated_vectors(manifest: Path, validation: Path) -> tuple[list[str], dict[str, int]]:
    validation_payload = json.loads(validation.read_text(encoding="utf-8"))
    if (
        validation_payload.get("status") != "valid"
        or validation_payload.get("hosts") != EXPECTED_HOSTS
        or validation_payload.get("manifest_sha256") != digest(manifest)
        or validation_payload.get("original_prefix_manifest_sha256") != PREFIX_MANIFEST_SHA256
        or validation_payload.get("aggregate_host_gate_schedule") != HOST_GATE_SCHEDULE
    ):
        raise AssertionError("census validation receipt is absent, incomplete, or bound to another manifest")
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row.get("host_index") for row in rows] != list(range(EXPECTED_HOSTS)):
        raise AssertionError("census manifest does not cover canonical hosts 0..655 exactly once")
    union: set[str] = set()
    occurrences = 0
    for index, row in enumerate(rows):
        if row.get("case") != expected_case(index):
            raise AssertionError(f"census case identity mismatch at host {index}")
        elapsed = float(row.get("host_seconds", 0))
        gate = expected_host_gate(index)
        if float(row.get("host_gate_seconds", 0)) != gate or not 0 < elapsed <= gate:
            raise AssertionError(f"invalid aggregate host gate at host {index}")
        artifact = Path(row["artifact"])
        if not artifact.is_absolute():
            artifact = manifest.parent / artifact
        if digest(artifact) != row.get("artifact_sha256"):
            raise AssertionError(f"host artifact hash mismatch at host {index}")
        with gzip.open(artifact, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        left = payload.get("bitset")
        right = payload.get("networkx_summary")
        if not isinstance(left, dict) or not isinstance(right, dict):
            raise AssertionError(f"malformed dual-enumerator artifact at host {index}")
        keys = ("embedding_count", "mapping_stream_sha256", "vector_occurrences", "unique_vector_count", "vector_stream_sha256")
        if any(left.get(key) != row.get(key) or right.get(key) != row.get(key) for key in keys):
            raise AssertionError(f"enumerator summary mismatch at host {index}")
        vectors = left.get("unique_vectors")
        if not isinstance(vectors, list) or vectors != sorted(set(vectors)):
            raise AssertionError(f"host vector stream is not sorted and unique at host {index}")
        for vector in vectors:
            vector_block(vector)
        if len(vectors) != row.get("unique_vector_count") or stream_digest(vectors) != row.get("vector_stream_sha256"):
            raise AssertionError(f"host vector stream receipt mismatch at host {index}")
        occurrences += int(row["vector_occurrences"])
        union.update(vectors)
        if len(union) > MAX_UNIQUE_VECTORS:
            raise RuntimeError(
                "global vector union exceeds the predeclared 10000-block memory/CNF pilot gate"
            )
    return sorted(union), {"hosts": len(rows), "vector_occurrences": occurrences}


def write_dimacs(path: Path, clauses: list[tuple[int, ...]]) -> None:
    with path.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(f"p cnf {TOTAL_VARIABLES} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(map(str, clause)) + " 0\n")


def clause_true(clause: tuple[int, ...], values: dict[int, bool]) -> bool:
    return any(values[abs(literal)] == (literal > 0) for literal in clause)


def parse_model(stdout: str) -> dict[int, bool]:
    values: dict[int, bool] = {}
    for line in stdout.splitlines():
        if line.startswith("v "):
            for text in line[2:].split():
                literal = int(text)
                if literal:
                    values[abs(literal)] = literal > 0
    if set(values) != set(range(1, TOTAL_VARIABLES + 1)):
        raise AssertionError("CaDiCaL returned an incomplete or out-of-range total model")
    return values


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=300)
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout)


def solver_limits(proof_file_limit_bytes: int = MAX_PROOF_FILE_BYTES) -> None:
    _set_child_limit(resource.RLIMIT_AS, 2 * 1024**3)
    _set_child_limit(resource.RLIMIT_FSIZE, proof_file_limit_bytes)


def _set_child_limit(kind: int, value: int) -> None:
    try:
        resource.setrlimit(kind, (value, value))
    except (OSError, ValueError):
        # Darwin does not implement every POSIX limit. The deployed Linux
        # lifecycle also enforces the declared cgroup limits independently.
        pass


def proof_checker_limits() -> None:
    _set_child_limit(resource.RLIMIT_AS, PROOF_CHECK_MEMORY_BYTES)
    _set_child_limit(resource.RLIMIT_FSIZE, PROOF_CHECK_LOG_BYTES)


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


def allocate_attempt_paths(requested_output: Path, requested_report: Path) -> tuple[Path, Path, int]:
    """Create a fresh immutable attempt without deleting interrupted predecessors."""
    requested_output.parent.mkdir(parents=True, exist_ok=True)
    requested_report.parent.mkdir(parents=True, exist_ok=True)
    for index in range(1_000_000):
        output = requested_output if index == 0 else requested_output.with_name(
            f"{requested_output.name}.attempt-{index:04d}"
        )
        report = requested_report if index == 0 else requested_report.with_name(
            f"{requested_report.stem}.attempt-{index:04d}{requested_report.suffix}"
        )
        if output.exists() or report.exists():
            continue
        try:
            output.mkdir()
        except FileExistsError:
            continue
        if report.exists():
            # Preserve the raced directory as an immutable collision marker.
            continue
        return output, report, index
    raise RuntimeError("could not allocate a fresh immutable residual-SAT attempt")


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
            handle.write("\nproof check timed out; result incomplete\n")
            handle.flush()
            os.fsync(handle.fileno())
            return None, time.monotonic() - started, True
    return checked, time.monotonic() - started, False


def sat_status(absent_from_controls: bool) -> str:
    return "sat_corpus_novel_candidate" if absent_from_controls else "sat_known_control"


def file_record(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def main() -> int:
    if len(sys.argv) != 13:
        raise SystemExit(
            "usage: run_known_class_residual_sat.py CENSUS_MANIFEST CENSUS_VALIDATION CORPUS "
            "CORPUS_REPORT CHECKER_A CHECKER_B_C CADICAL DRAT_TRIM OUTPUT_DIR REPORT "
            "SOLVE_SECONDS SEED"
        )
    (
        manifest, validation, corpus, corpus_report, checker_a, checker_b_source,
        cadical, drat_trim, output_dir, report,
    ) = map(Path, sys.argv[1:11])
    solve_seconds, seed = map(int, sys.argv[11:13])
    if not 1 <= solve_seconds <= MAX_SOLVE_SECONDS or seed != 1:
        raise ValueError("require a 1..3600 second bounded solve and the predeclared seed 1")
    requested_output_dir, requested_report = output_dir, report
    required = (manifest, validation, corpus, corpus_report, checker_a, checker_b_source, cadical, drat_trim)
    if any(not path.is_file() for path in required):
        raise FileNotFoundError("one or more immutable inputs/tools are absent")
    if digest(corpus) != CORPUS_SHA256:
        raise AssertionError("authenticated corpus hash mismatch")
    records = corpus.read_bytes().splitlines()
    if len(records) != 328:
        raise AssertionError("authenticated corpus does not contain 328 records")
    retained = json.loads(corpus_report.read_text(encoding="utf-8"))
    if retained.get("canonical_distinct_classes") != EXPECTED_HOSTS:
        raise AssertionError("authenticated corpus report does not retain 656 classes")

    vectors, census_counts = load_validated_vectors(manifest, validation)
    if not vectors:
        raise AssertionError("complete census supplied no class blocks")
    source_graphs = [parse_graph6(record) for record in records]
    source = source_graphs[SOURCE_RECORD - 1]
    source_control_vector = row_sorted_source_vector(source)
    if source_control_vector not in vectors:
        raise AssertionError("complete census omits the row-sorted record-21 positive-control vector")
    base_clauses, _row_pairs = build_formula(source)
    blocks = [vector_block(vector) for vector in vectors]
    all_clauses = base_clauses + blocks

    disk_probe = output_dir.parent
    while not disk_probe.exists() and disk_probe != disk_probe.parent:
        disk_probe = disk_probe.parent
    free_bytes = shutil.disk_usage(disk_probe).free
    proof_file_limit_bytes = min(
        MAX_PROOF_FILE_BYTES,
        free_bytes - ROOT_DISK_RESERVE_BYTES - NONPROOF_HEADROOM_BYTES,
    )
    if proof_file_limit_bytes < 256 * 1024**2:
        raise RuntimeError(
            "insufficient disk headroom for proof logging while preserving the 8 GiB root reserve"
        )

    output_dir, report, attempt_index = allocate_attempt_paths(requested_output_dir, requested_report)
    attempt_state = output_dir / "attempt-state.json"
    atomic_json(attempt_state, {
        "schema_version": 1,
        "status": "running",
        "attempt_index": attempt_index,
        "requested_output": str(requested_output_dir),
        "requested_report": str(requested_report),
        "actual_output": str(output_dir),
        "actual_report": str(report),
        "command": [sys.executable, *sys.argv],
        "producer_sha256": digest(Path(__file__)),
        "started_unix": time.time(),
    })
    block_ledger = output_dir / "known-primary-vectors.txt.gz"
    with gzip.open(block_ledger, "wt", encoding="ascii", newline="\n") as handle:
        for vector in vectors:
            handle.write(vector + "\n")
    cnf = output_dir / "record-21-lex-known-classes-blocked.cnf"
    write_dimacs(cnf, all_clauses)
    proof = output_dir / "cadical.drat"
    solver_stdout = output_dir / "cadical.stdout"
    solver_stderr = output_dir / "cadical.stderr"

    started = time.monotonic()
    solved = subprocess.run(
        [str(cadical), "-q", "-t", str(solve_seconds), f"--seed={seed}", str(cnf), str(proof)],
        text=True,
        capture_output=True,
        preexec_fn=lambda: solver_limits(proof_file_limit_bytes),
    )
    solver_seconds = time.monotonic() - started
    solver_stdout.write_text(solved.stdout, encoding="ascii")
    solver_stderr.write_text(solved.stderr, encoding="ascii")
    if not proof.exists():
        proof.write_bytes(b"")

    result: dict[str, object]
    if solved.returncode == 10 and "s SATISFIABLE" in solved.stdout:
        values = parse_model(solved.stdout)
        if not all(clause_true(clause, values) for clause in all_clauses):
            raise AssertionError("SAT model falsifies the physical blocked DIMACS")
        candidate = [row[:] for row in source]
        for variable, (u, v) in enumerate(boundary_edges(), 1):
            candidate[u][v] = candidate[v][u] = values[variable]
        rows = [tuple(int(candidate[vertex][core]) for core in FIXED) for vertex in DESTROY]
        if rows != sorted(rows):
            raise AssertionError("SAT model violates direct S_12 row order")
        candidate_path = output_dir / "candidate.g6"
        candidate_path.write_bytes(encode_graph6(candidate))
        compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        labelg = shutil.which("nauty-labelg")
        if compiler is None or labelg is None:
            raise RuntimeError("a C compiler and nauty-labelg are required for SAT validation")
        with tempfile.TemporaryDirectory(prefix="r55-residual-sat-") as temporary_name:
            temporary = Path(temporary_name)
            checker_b = temporary / "checker_b"
            subprocess.run(
                [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)],
                check=True,
            )
            left = run_json([sys.executable, str(checker_a), "--format", "graph6", "--input", str(candidate_path)])
            right = run_json([str(checker_b), "--format", "graph6", "--input", str(candidate_path)])
            if left["graphs"][0] != right["graphs"][0] or left["graphs"][0]["zero_k5"] or left["graphs"][0]["one_k5"]:
                raise AssertionError("independent full-graph checkers reject the SAT candidate")
            controls = temporary / "controls.g6"
            controls.write_bytes(
                b"".join(record + b"\n" for record in records)
                + b"".join(encode_graph6(complement(graph)) for graph in source_graphs)
            )
            canonical_controls = temporary / "controls.canonical.g6"
            subprocess.run([labelg, "-q", str(controls), str(canonical_controls)], check=True)
            control_set = set(canonical_controls.read_bytes().splitlines())
            if len(control_set) != EXPECTED_HOSTS:
                raise AssertionError("nauty control set does not contain 656 distinct classes")
            canonical_path = output_dir / "candidate.canonical.g6"
            subprocess.run([labelg, "-q", str(candidate_path), str(canonical_path)], check=True)
            canonical = canonical_path.read_bytes().strip()
        model_path = output_dir / "model.json"
        model_path.write_text(json.dumps({str(k): values[k] for k in sorted(values)}, sort_keys=True) + "\n", encoding="ascii")
        absent_from_controls = canonical not in control_set
        result = {
            "status": sat_status(absent_from_controls),
            "candidate": file_record(candidate_path),
            "canonical_candidate": file_record(canonical_path),
            "model": file_record(model_path),
            "nauty_canonical_absent_from_supplied_656": absent_from_controls,
            "physical_dimacs_satisfied": True,
            "direct_row_order": True,
            "python_and_c_full_graph_checks_agree": True,
            "claim_limit": (
                "candidate only; absence is relative to the supplied 656 classes and requires cold audit and human novelty review"
                if absent_from_controls else
                "known supplied-corpus control; the discriminator produced no candidate contribution"
            ),
        }
    elif solved.returncode == 20 and "s UNSATISFIABLE" in solved.stdout:
        checker_log = output_dir / "drat-trim.log"
        checked, proof_check_seconds, proof_check_timed_out = run_drat_check(
            drat_trim, cnf, proof, checker_log
        )
        checker_text = checker_log.read_text(encoding="utf-8")
        if proof_check_timed_out:
            result = {
                "status": "unknown",
                "returncode": solved.returncode,
                "reason": "proof_check_timeout",
                "proof": file_record(proof),
                "proof_bytes_preserved": proof.stat().st_size,
                "proof_check": file_record(checker_log),
                "proof_check_seconds": proof_check_seconds,
                "claim_limit": "UNSAT proof checking timed out; no mathematical conclusion",
            }
        elif checked is None or checked.returncode != 0 or "s VERIFIED" not in checker_text:
            result = {
                "status": "unknown",
                "returncode": solved.returncode,
                "reason": "proof_check_failed",
                "proof": file_record(proof),
                "proof_bytes_preserved": proof.stat().st_size,
                "proof_check": file_record(checker_log),
                "proof_check_seconds": proof_check_seconds,
                "proof_check_returncode": None if checked is None else checked.returncode,
                "claim_limit": "UNSAT proof checking failed; no mathematical conclusion",
            }
        else:
            result = {
                "status": "unsat_verified",
                "proof": file_record(proof),
                "proof_check": file_record(checker_log),
                "proof_check_seconds": proof_check_seconds,
                "proof_check_limits": {
                    "wall_seconds": PROOF_CHECK_SECONDS,
                    "memory_bytes": PROOF_CHECK_MEMORY_BYTES,
                    "log_bytes": PROOF_CHECK_LOG_BYTES,
                },
                "claim_limit": "excludes only the record-21 frozen-core S_12 row-lex quotient after blocking every exact vector in the validated supplied-class census",
            }
    else:
        result = {
            "status": "unknown",
            "returncode": solved.returncode,
            "proof_bytes_preserved": proof.stat().st_size,
            "claim_limit": "timeout or solver failure is inconclusive and supports no mathematical claim",
        }

    payload = {
        "schema_version": 1,
        "status": "known_class_residual_sat_complete",
        "scope": "record-21 frozen order-30 core; exact S_12 destroyed-row lex quotient; complete validated supplied-corpus vector blocks",
        "inputs": {
            "census_manifest": file_record(manifest),
            "census_validation": file_record(validation),
            "corpus": file_record(corpus),
            "corpus_report": file_record(corpus_report),
            "checker_a": file_record(checker_a),
            "checker_b_source": file_record(checker_b_source),
            "cadical": file_record(cadical),
            "drat_trim": file_record(drat_trim),
        },
        "census": {
            **census_counts,
            "unique_primary_vectors": len(vectors),
            "row_sorted_record_21_vector_present": True,
            "block_ledger": file_record(block_ledger),
            "all_vectors_exactly_426_bits": True,
        },
        "formula": {
            "primary_variables": PRIMARY_VARIABLES,
            "total_variables": TOTAL_VARIABLES,
            "base_clauses": len(base_clauses),
            "class_blocks": len(blocks),
            "total_clauses": len(all_clauses),
            "cnf": file_record(cnf),
            "hamming_constraint_present": False,
        },
        "solver": {
            "name": "CaDiCaL",
            "version": subprocess.run([str(cadical), "--version"], text=True, capture_output=True, check=True).stdout.strip(),
            "seed": seed,
            "wall_limit_seconds": solve_seconds,
            "memory_limit_bytes": 2 * 1024**3,
            "proof_file_limit_bytes": proof_file_limit_bytes,
            "root_disk_reserve_bytes": ROOT_DISK_RESERVE_BYTES,
            "nonproof_headroom_bytes": NONPROOF_HEADROOM_BYTES,
            "returncode": solved.returncode,
            "seconds": solver_seconds,
            "stdout": file_record(solver_stdout),
            "stderr": file_record(solver_stderr),
        },
        "result": result,
        "claim_limit": "no conclusion beyond this fixed-core quotient; UNKNOWN is inconclusive; SAT novelty is not established by corpus nonmembership alone",
    }
    atomic_json(report, payload)
    atomic_json(attempt_state, {
        "schema_version": 1,
        "status": "completed",
        "attempt_index": attempt_index,
        "requested_output": str(requested_output_dir),
        "requested_report": str(requested_report),
        "actual_output": str(output_dir),
        "actual_report": str(report),
        "command": [sys.executable, *sys.argv],
        "producer_sha256": digest(Path(__file__)),
        "report_sha256": digest(report),
        "result_status": result["status"],
        "completed_unix": time.time(),
    })
    print(json.dumps({"status": result["status"], "vectors": len(vectors), "report": str(report), "report_sha256": digest(report)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
