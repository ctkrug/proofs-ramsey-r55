#!/usr/bin/env python3
"""Incremental labelled-model CEGAR for one frozen order-42 boundary.

The immutable base CNF is the retained trial-1 formula from epoch 14.  After
each independently checked supplied-corpus model, this controller appends one
426-literal clause blocking exactly that primary assignment.  Canonical graph
labels are an acceptance test only: no clause in this program blocks an
isomorphism class.
"""

from __future__ import annotations

import gzip
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
PRIMARY_VARIABLES = 426
TOTAL_VARIABLES = 155_976
BASE_CLAUSES = 508_157
MINIMUM_DISTANCE = 60
SOURCE_RECORD = 21
FINGERPRINT = "r55novel42basin2026"
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
BASE_LOGICAL_SHA256 = "2f1c3b2ac59e4c4b6e2873d2d5ebb2d2eba4fd908a2927f2a30d1936bc3d1072"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def logical_digest(path: Path) -> str:
    value = hashlib.sha256()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def stable_sample(label: str, population: list[int], count: int) -> list[int]:
    ranked = sorted(population, key=lambda item: hashlib.sha256(f"{FINGERPRINT}:{label}:{item}".encode()).digest())
    return sorted(ranked[:count])


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


def model_value(packed: bytes, variable: int) -> bool:
    bit = variable - 1
    return bool((packed[bit // 8] >> (bit % 8)) & 1)


def packed_primary(packed: bytes) -> bytes:
    output = bytearray((PRIMARY_VARIABLES + 7) // 8)
    for variable in range(1, PRIMARY_VARIABLES + 1):
        if model_value(packed, variable):
            bit = variable - 1
            output[bit // 8] |= 1 << (bit % 8)
    return bytes(output)


def literal_true(packed: bytes, literal: int) -> bool:
    value = model_value(packed, abs(literal))
    return value if literal > 0 else not value


def check_base_cnf(path: Path, packed: bytes) -> dict[str, int | bool]:
    variables = expected_clauses = clauses = None
    counted = 0
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as stream:
        for line_number, raw in enumerate(stream, 1):
            if raw.startswith("p cnf "):
                _, _, var_text, clause_text = raw.split()
                variables, expected_clauses = int(var_text), int(clause_text)
                continue
            if not raw.strip() or raw.startswith("c"):
                continue
            literals = [int(text) for text in raw.split()]
            if not literals or literals[-1] != 0:
                raise AssertionError(f"malformed DIMACS line {line_number}")
            literals.pop()
            if not any(literal_true(packed, literal) for literal in literals):
                raise AssertionError(f"model falsifies base DIMACS clause at line {line_number}")
            counted += 1
    if variables != TOTAL_VARIABLES or expected_clauses != BASE_CLAUSES or counted != BASE_CLAUSES:
        raise AssertionError("base DIMACS header/count mismatch")
    return {"variables": variables, "clauses": counted, "satisfied": True}


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=180)
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout)


def limit_enumerator() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024**2, 256 * 1024**2))


def main() -> int:
    if len(sys.argv) != 12:
        raise SystemExit(
            "usage: run_novel42_labelled_cegar.py CORPUS CORPUS_REPORT BASE_CNF_GZ "
            "CHECKER_A CHECKER_B_C ENUMERATOR_CPP OUTPUT_DIR REPORT MAX_MODELS "
            "SOLVE_SECONDS SEED"
        )
    corpus, corpus_report, base_cnf, checker_a, checker_b_source, enumerator_source, output_dir, report = map(
        Path, sys.argv[1:9]
    )
    max_models, solve_seconds, seed = map(int, sys.argv[9:12])
    if not 1 <= max_models <= 64 or solve_seconds <= 0 or seed <= 0:
        raise ValueError("require 1..64 models and positive solve limit/seed")
    if output_dir.exists() or report.exists():
        raise ValueError("output directory or report already exists")
    if digest(corpus) != CORPUS_SHA256:
        raise AssertionError("authenticated corpus hash mismatch")
    if logical_digest(base_cnf) != BASE_LOGICAL_SHA256:
        raise AssertionError("retained trial-1 logical CNF hash mismatch")
    retained = json.loads(corpus_report.read_text(encoding="utf-8"))
    if retained.get("canonical_distinct_classes") != 656:
        raise AssertionError("retained corpus report mismatch")

    compiler = shutil.which("g++")
    labelg = shutil.which("nauty-labelg")
    if not compiler or not labelg:
        raise RuntimeError("g++ and nauty-labelg are required")
    records = corpus.read_bytes().splitlines()
    if len(records) != 328:
        raise AssertionError("expected 328 source graph6 records")
    source_graphs = [parse_graph6(record) for record in records]
    source = source_graphs[SOURCE_RECORD - 1]
    destroy = stable_sample(f"destroy:{SOURCE_RECORD - 1}", list(range(ORDER)), 12)
    destroyed = set(destroy)
    variable_edges = [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed or high in destroyed
    ]
    if len(variable_edges) != PRIMARY_VARIABLES:
        raise AssertionError("primary boundary mapping mismatch")

    output_dir.mkdir(parents=True)
    shutil.copyfile(base_cnf, output_dir / "base.cnf.gz")
    controls = source_graphs + [complement(graph) for graph in source_graphs]
    with tempfile.TemporaryDirectory(prefix="r55-labelled-cegar-") as temporary:
        temp = Path(temporary)
        checker_b = temp / "checker_b"
        enumerator = temp / "incremental-enumerator"
        subprocess.run(
            ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)],
            check=True,
        )
        subprocess.run(
            [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", str(enumerator_source), "-lcadical", "-o", str(enumerator)],
            check=True,
        )
        controls_path = temp / "controls.g6"
        controls_path.write_bytes(b"".join(record + b"\n" for record in records) + b"".join(encode_graph6(g) for g in controls[328:]))
        canonical_controls_path = temp / "controls.canonical.g6"
        subprocess.run([labelg, "-q", str(controls_path), str(canonical_controls_path)], check=True)
        canonical_controls = set(canonical_controls_path.read_bytes().splitlines())
        if len(canonical_controls) != 656:
            raise AssertionError("canonical control set mismatch")
        canonical_lookup: dict[str, tuple[int, str]] = {}
        for entry in retained["per_record_manifest"]:
            record = int(entry["record"])
            for kind in ("source", "complement"):
                canonical_lookup[entry[f"{kind}_canonical_sha256"]] = (record, kind)

        uncompressed_base = temp / "base.cnf"
        with gzip.open(base_cnf, "rb") as src, uncompressed_base.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        stderr_path = output_dir / "incremental-enumerator.stderr"
        stderr_stream = stderr_path.open("w", encoding="utf-8")
        process = subprocess.Popen(
            [
                str(enumerator), str(uncompressed_base), str(output_dir), str(TOTAL_VARIABLES),
                str(PRIMARY_VARIABLES), str(max_models), str(seed), str(solve_seconds),
            ],
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_stream,
            preexec_fn=limit_enumerator,
        )
        if process.stdin is None or process.stdout is None:
            raise AssertionError("failed to open enumerator protocol")
        blocks: list[list[int]] = []
        models: list[dict[str, object]] = []
        primary_hashes: set[str] = set()
        witness: dict[str, object] | None = None
        terminal_status = "model_budget_reached"
        for expected_round in range(1, max_models + 1):
            line = process.stdout.readline()
            if not line:
                raise RuntimeError("incremental enumerator ended without a status line")
            solver = json.loads(line)
            if solver.get("round") != expected_round:
                raise AssertionError("incremental round mismatch")
            if solver.get("status") != "SAT":
                terminal_status = str(solver.get("status", "malformed_solver_status")).lower()
                process.stdin.write("STOP\n") if process.poll() is None else None
                process.stdin.flush() if process.poll() is None else None
                break
            model_path = output_dir / str(solver["model"])
            packed = model_path.read_bytes()
            if len(packed) != (TOTAL_VARIABLES + 7) // 8:
                raise AssertionError("packed total model has wrong size")
            primary = packed_primary(packed)
            primary_hash = hashlib.sha256(primary).hexdigest()
            if primary_hash in primary_hashes:
                raise AssertionError("a blocked primary assignment was repeated")
            primary_hashes.add(primary_hash)
            for earlier in blocks:
                if not any(literal_true(packed, literal) for literal in earlier):
                    raise AssertionError("new model falsifies a prior primary block")
            cnf_check = check_base_cnf(base_cnf, packed)

            candidate = [row[:] for row in source]
            for variable, (u, v) in enumerate(variable_edges, 1):
                candidate[u][v] = candidate[v][u] = model_value(packed, variable)
            distance = sum(candidate[u][v] != source[u][v] for u, v in variable_edges)
            fixed_equal = all(
                candidate[u][v] == source[u][v]
                for u, v in itertools.combinations(range(ORDER), 2)
                if u not in destroyed and v not in destroyed
            )
            if distance < MINIMUM_DISTANCE or not fixed_equal:
                raise AssertionError("decoded model violates boundary scope")
            candidate_path = output_dir / f"candidate-{expected_round:03d}.g6"
            candidate_path.write_bytes(encode_graph6(candidate))
            payload_a = run_json([sys.executable, str(checker_a), "--format", "graph6", "--input", str(candidate_path)])
            payload_b = run_json([str(checker_b), "--format", "graph6", "--input", str(candidate_path)])
            checked_a, checked_b = payload_a["graphs"][0], payload_b["graphs"][0]
            if checked_a != checked_b or checked_a["zero_k5"] or checked_a["one_k5"]:
                raise AssertionError("full graph checker failure or disagreement")
            canonical_path = output_dir / f"candidate-{expected_round:03d}.canonical.g6"
            subprocess.run([labelg, "-q", str(candidate_path), str(canonical_path)], check=True)
            canonical = canonical_path.read_bytes().strip()
            canonical_novel = canonical not in canonical_controls
            canonical_file_hash = digest(canonical_path)
            target = canonical_lookup.get(canonical_file_hash)
            if canonical_novel != (target is None):
                raise AssertionError("canonical lookup representations disagree")

            block = [(-variable if model_value(packed, variable) else variable) for variable in range(1, PRIMARY_VARIABLES + 1)]
            if any(literal_true(packed, literal) for literal in block):
                raise AssertionError("new primary block does not falsify its source model")
            block_line = " ".join(map(str, block)) + " 0\n"
            block_hash = hashlib.sha256(block_line.encode("ascii")).hexdigest()
            entry: dict[str, object] = {
                "round": expected_round,
                "solver_seconds": solver["seconds"],
                "solver_library": solver["cadical_version"],
                "model_bits_path": str(model_path.relative_to(output_dir.parent)),
                "model_bits_sha256": digest(model_path),
                "primary_vector_sha256": primary_hash,
                "candidate_path": str(candidate_path.relative_to(output_dir.parent)),
                "candidate_graph6_sha256": digest(candidate_path),
                "canonical_path": str(canonical_path.relative_to(output_dir.parent)),
                "canonical_sha256": canonical_file_hash,
                "actual_boundary_hamming_distance": distance,
                "fixed_induced_order_30_equal": fixed_equal,
                "base_cnf_model": cnf_check,
                "prior_blocks_satisfied": len(blocks),
                "python_direct_five_subset_scan": True,
                "c_recursive_bitset_scan": True,
                "nauty_canonical_absent_from_supplied_656": canonical_novel,
                "supplied_target": None if target is None else {"record": target[0], "kind": target[1]},
                "block_sha256": block_hash if not canonical_novel else None,
                "block_scope": "one labelled 426-bit primary assignment" if not canonical_novel else None,
            }
            models.append(entry)
            if canonical_novel:
                witness = entry
                terminal_status = "supplied_corpus_novel_valid_order42"
                process.stdin.write("STOP\n")
                process.stdin.flush()
                break
            blocks.append(block)
            with (output_dir / "blocks.dimacs").open("a", encoding="ascii", newline="\n") as stream:
                stream.write(block_line)
            if expected_round == max_models:
                process.stdin.write("STOP\n")
                process.stdin.flush()
            else:
                process.stdin.write("CONTINUE\n")
                process.stdin.flush()

        returncode = process.wait(timeout=30)
        stderr_stream.close()
        if returncode != 0:
            raise RuntimeError(f"incremental enumerator exited {returncode}: {stderr_path.read_text(encoding='utf-8')}")

    blocks_path = output_dir / "blocks.dimacs"
    if not blocks_path.exists():
        blocks_path.write_text("", encoding="ascii")
    payload = {
        "schema_version": 1,
        "status": "novel42_labelled_cegar_complete",
        "result": terminal_status,
        "scope": "one frozen labelled 30-vertex core from source record 21; at most 64 incrementally enumerated boundary completions",
        "claim_limit": "each 426-literal block excludes one labelled completion only; it is not an isomorphism-class block or a boundary exclusion",
        "hypothesis": "within 64 verified labelled completions, the retained boundary yields a valid Ramsey(5,5,42) graph absent from the supplied 656 classes",
        "corpus": {"path": str(corpus), "sha256": digest(corpus), "canonical_classes": 656},
        "base_cnf": {
            "input_path": str(base_cnf), "retained_copy": str(output_dir / "base.cnf.gz"),
            "logical_sha256": logical_digest(base_cnf), "variables": TOTAL_VARIABLES,
            "clauses": BASE_CLAUSES, "primary_variables": PRIMARY_VARIABLES,
        },
        "boundary": {
            "source_record": SOURCE_RECORD, "destroy_vertices": destroy, "fixed_vertices": 30,
            "variable_edges": PRIMARY_VARIABLES, "minimum_hamming_distance": MINIMUM_DISTANCE,
        },
        "incremental_protocol": {
            "seed": seed, "per_solve_wall_limit_seconds": solve_seconds, "model_budget": max_models,
            "blocks_appended": len(blocks), "block_literals": PRIMARY_VARIABLES,
            "base_parsed_once": True, "learned_clauses_reused_within_boundary": True,
        },
        "models": models,
        "witness": witness,
        "distinct_primary_vectors": len(primary_hashes),
        "distinct_supplied_targets": len({(m["supplied_target"]["record"], m["supplied_target"]["kind"]) for m in models if m["supplied_target"]}),
        "blocks_path": str(blocks_path),
        "blocks_sha256": digest(blocks_path),
        "delegate_memo_correction": {
            "memo_value": "2f1c3b2ac59e28c4b6e2873d2d5ebb2d2eba4fd908a2927f2a30d1936bc3d1072",
            "artifact_value": BASE_LOGICAL_SHA256,
            "resolution": "used the retained artifact and production report; the experiment-verification memo contains a transcription error",
        },
        "embedding_census": {
            "status": "not_completed",
            "naive_deleted_subsets_per_control": 11_058_116_888,
            "reason": "exact negative induced-subgraph probes were already slower than a SAT model and yielded no compact all-embedding class block; census is interpretive, not required for labelled blocking",
        },
        "search_efficiency": {
            "unfrozen_edge_variables": 861, "frozen_core_edges": 435, "boundary_primary_variables": 426,
            "primary_reduction_fraction": 435 / 861, "base_ramsey_five_sets_skipped": 142_506,
            "blocks_added_at_most": max_models,
            "chosen_mechanism": "incremental CaDiCaL: parse the base once, retain learned clauses, append one long primary block per verified known model",
        },
        "independence": {
            "producer": str(Path(__file__).resolve()),
            "enumerator_source": {"path": str(enumerator_source), "sha256": digest(enumerator_source)},
            "checker_a": {"path": str(checker_a), "sha256": digest(checker_a)},
            "checker_b": {"path": str(checker_b_source), "sha256": digest(checker_b_source)},
            "per_model_gates": ["full base DIMACS evaluation", "all prior block evaluation", "Python five-subset scan", "C recursive-bitset scan", "nauty canonical membership"],
        },
        "tool_versions": {
            "python": sys.version.split()[0],
            "g++": subprocess.run([compiler, "--version"], text=True, capture_output=True).stdout.splitlines()[0],
            "libcadical": models[0]["solver_library"] if models else "no SAT model",
        },
    }
    report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"], "result": payload["result"], "models": len(models),
        "distinct_supplied_targets": payload["distinct_supplied_targets"], "witness": witness,
        "report": str(report), "report_sha256": digest(report),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
