#!/usr/bin/env python3
"""Independent replay audit for the two-record known-class embedding pilot.

The checker imports neither enumerator.  It reparses graph6, validates every
embedding and pullback, compares complete streams, tests historical controls,
and invokes the two established exact R(5,5) graph checkers.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile


ORDER = 42
DESTROY = [2, 3, 10, 12, 14, 25, 27, 30, 36, 37, 38, 41]
FIXED = sorted(set(range(ORDER)) - set(DESTROY))
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
SORTED_SOURCE_SHA256 = "8672d9a6204722aaae23bbded698fd3b4ec1aa67d71b9c7baec4cddf63cdad5e"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stream_hash(lines: list[str]) -> str:
    return data_hash(b"".join((line + "\n").encode("ascii") for line in lines))


def parse_graph6(raw: bytes) -> list[list[bool]]:
    if not raw or any(byte < 63 or byte > 126 for byte in raw):
        raise ValueError("bad graph6 byte")
    n = raw[0] - 63
    if not 1 <= n <= 62:
        raise ValueError("unsupported graph6 header")
    total = n * (n - 1) // 2
    if len(raw) != 1 + (total + 5) // 6:
        raise ValueError("wrong graph6 length")
    graph = [[False] * n for _ in range(n)]
    for cursor, (high, low) in enumerate((high, low) for high in range(1, n) for low in range(high)):
        encoded = raw[1 + cursor // 6] - 63
        edge = bool((encoded >> (5 - cursor % 6)) & 1)
        graph[low][high] = graph[high][low] = edge
    for cursor in range(total, ((total + 5) // 6) * 6):
        encoded = raw[1 + cursor // 6] - 63
        if (encoded >> (5 - cursor % 6)) & 1:
            raise ValueError("nonzero graph6 padding")
    return graph


def encode_graph6(graph: list[list[bool]]) -> bytes:
    n = len(graph)
    bits = [int(graph[low][high]) for high in range(1, n) for low in range(high)]
    while len(bits) % 6:
        bits.append(0)
    body = bytearray()
    for offset in range(0, len(bits), 6):
        value = 0
        for bit in bits[offset:offset + 6]:
            value = (value << 1) | bit
        body.append(value + 63)
    return bytes([n + 63]) + bytes(body) + b"\n"


def complement(graph: list[list[bool]]) -> list[list[bool]]:
    return [[i != j and not graph[i][j] for j in range(len(graph))] for i in range(len(graph))]


def boundary_edges() -> list[tuple[int, int]]:
    destroy = set(DESTROY)
    return [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroy or high in destroy
    ]


def reconstruct_labelled(source: list[list[bool]], vector: str) -> list[list[bool]]:
    if len(vector) != 426 or set(vector) - {"0", "1"}:
        raise AssertionError("malformed boundary vector")
    graph = [[False] * ORDER for _ in range(ORDER)]
    for offset, (low, high) in enumerate(boundary_edges()):
        graph[low][high] = graph[high][low] = vector[offset] == "1"
    for high_index, high in enumerate(FIXED):
        for low in FIXED[:high_index]:
            graph[low][high] = graph[high][low] = source[low][high]
    return graph


def replay_entry(
    source: list[list[bool]], host: list[list[bool]], entry: dict[str, object]
) -> tuple[list[str], list[list[int]]]:
    mapping = [int(value) for value in entry["map_pattern_to_host"]]
    if len(mapping) != 30 or len(set(mapping)) != 30 or any(not 0 <= value < ORDER for value in mapping):
        raise AssertionError("embedding is not an injection of the core")
    for high in range(1, 30):
        for low in range(high):
            if source[FIXED[low]][FIXED[high]] != host[mapping[low]][mapping[high]]:
                raise AssertionError("map is not an induced-core embedding")
    residual = sorted(set(range(ORDER)) - set(mapping))
    rows = {
        vertex: tuple(host[vertex][mapping[position]] for position in range(30))
        for vertex in residual
    }
    ordered = sorted(residual, key=lambda vertex: (rows[vertex], vertex))
    groups = [list(group) for _row, group in itertools.groupby(ordered, key=lambda vertex: rows[vertex])]
    expected_orders = sorted(
        [vertex for choice in choices for vertex in choice]
        for choices in itertools.product(*(list(itertools.permutations(group)) for group in groups))
    )
    actual_orders = sorted([[int(value) for value in order] for order in entry["residual_orders"]])
    if expected_orders != actual_orders:
        raise AssertionError("residual-order list omits or adds a tied-row permutation")
    expected_sizes = [len(group) for group in groups]
    if entry["tie_group_sizes"] != expected_sizes:
        raise AssertionError("tie-group signature mismatch")
    multiplicity = math.prod(math.factorial(size) for size in expected_sizes)
    if int(entry["tie_multiplicity"]) != multiplicity:
        raise AssertionError("tie multiplicity mismatch")
    actual_vectors = [str(vector) for vector in entry["vectors"]]
    if len(actual_vectors) != len(actual_orders):
        raise AssertionError("order/vector arity mismatch")

    expected_vectors: list[str] = []
    for order in [[int(value) for value in order] for order in entry["residual_orders"]]:
        if [rows[vertex] for vertex in order] != sorted(rows[vertex] for vertex in order):
            raise AssertionError("recorded residual order is not row-lex accepted")
        pullback = {label: mapping[position] for position, label in enumerate(FIXED)}
        pullback.update(zip(DESTROY, order, strict=True))
        if len(set(pullback.values())) != ORDER:
            raise AssertionError("pullback is not a bijection")
        vector = "".join(
            "1" if host[pullback[low]][pullback[high]] else "0"
            for low, high in boundary_edges()
        )
        expected_vectors.append(vector)
        labelled = reconstruct_labelled(source, vector)
        for high in range(1, ORDER):
            for low in range(high):
                if labelled[low][high] != host[pullback[low]][pullback[high]]:
                    raise AssertionError("reconstructed graph differs from host under pullback")
    if expected_vectors != actual_vectors:
        raise AssertionError("recorded boundary vector differs from exact pullback")
    return expected_vectors, actual_orders


def validate_case(source: list[list[bool]], host: list[list[bool]], case: dict[str, object]) -> dict[str, object]:
    entries = case["embeddings"]
    maps = [tuple(int(value) for value in entry["map_pattern_to_host"]) for entry in entries]
    if maps != sorted(maps) or len(maps) != len(set(maps)) or len(maps) != int(case["embedding_count"]):
        raise AssertionError("embedding stream is not exact sorted unique data")
    all_vectors: list[str] = []
    for entry in entries:
        vectors, _orders = replay_entry(source, host, entry)
        all_vectors.extend(vectors)
    unique = sorted(set(all_vectors))
    if unique != case["unique_vectors"] or len(unique) != int(case["unique_vector_count"]):
        raise AssertionError("unique vector stream mismatch")
    if len(all_vectors) != int(case["vector_occurrences"]):
        raise AssertionError("vector occurrence count mismatch")
    mapping_lines = [",".join(map(str, mapping)) for mapping in maps]
    if stream_hash(mapping_lines) != case["mapping_stream_sha256"]:
        raise AssertionError("mapping stream hash mismatch")
    if stream_hash(unique) != case["vector_stream_sha256"]:
        raise AssertionError("vector stream hash mismatch")
    return {
        "embedding_count": len(maps),
        "vector_occurrences": len(all_vectors),
        "unique_vector_count": len(unique),
        "mapping_stream_sha256": case["mapping_stream_sha256"],
        "vector_stream_sha256": case["vector_stream_sha256"],
    }


def run_json(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, check=True, text=True, capture_output=True, timeout=120)
    if completed.stderr:
        raise RuntimeError(f"unexpected checker stderr: {completed.stderr}")
    return json.loads(completed.stdout)


def main() -> int:
    if len(sys.argv) != 9:
        raise SystemExit(
            "usage: known_class_embedding_pilot_audit.py CORPUS BITSET_MANIFEST NX_MANIFEST SORTED_SOURCE CANDIDATE CHECKER_A CHECKER_B OUTPUT"
        )
    corpus_path, bitset_path, nx_path, sorted_source_path, candidate_path, checker_a, checker_b, output = map(Path, sys.argv[1:])
    if file_hash(corpus_path) != CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")
    if file_hash(sorted_source_path) != SORTED_SOURCE_SHA256:
        raise AssertionError("retained row-sorted source hash mismatch")
    corpus = [parse_graph6(line) for line in corpus_path.read_bytes().splitlines()]
    if len(corpus) != 328:
        raise AssertionError("wrong corpus cardinality")
    source = corpus[20]
    hosts = {
        "source_record_21": source,
        "source_record_12": corpus[11],
        "complement_record_21": complement(source),
    }
    manifests = [
        json.loads(bitset_path.read_text(encoding="utf-8")),
        json.loads(nx_path.read_text(encoding="utf-8")),
    ]
    for manifest in manifests:
        if manifest["corpus_sha256"] != CORPUS_SHA256 or manifest["core_fixed_labels"] != FIXED or manifest["destroy_labels"] != DESTROY:
            raise AssertionError("manifest scope mismatch")
    bitset_cases = {case["case"]: case for case in manifests[0]["cases"]}
    nx_cases = {case["case"]: case for case in manifests[1]["cases"]}
    if set(bitset_cases) != set(hosts) or set(nx_cases) != set(hosts):
        raise AssertionError("case-set mismatch")
    comparisons: dict[str, object] = {}
    for name, host in hosts.items():
        left, right = bitset_cases[name], nx_cases[name]
        left_exact = {key: value for key, value in left.items() if key not in {"seconds", "search_stats"}}
        right_exact = {key: value for key, value in right.items() if key not in {"seconds", "search_stats"}}
        if left_exact != right_exact:
            raise AssertionError(f"independent exact streams differ for {name}")
        comparisons[name] = validate_case(source, host, left)
    if comparisons["complement_record_21"]["embedding_count"] != 0:
        raise AssertionError("negative control contains the core")

    # Historical source control: the identity core embedding and its sorted
    # residual order must reproduce the retained row-sorted graph byte exactly.
    identity_entry = next(
        entry for entry in bitset_cases["source_record_21"]["embeddings"]
        if entry["map_pattern_to_host"] == FIXED
    )
    identity_vector = identity_entry["vectors"][0]
    identity_graph = reconstruct_labelled(source, identity_vector)
    if encode_graph6(identity_graph) != sorted_source_path.read_bytes():
        raise AssertionError("identity embedding does not reproduce retained sorted source")

    # Historical record-12 control: the stored SAT candidate is already in the
    # fixed boundary and direct row order; its exact primary vector must occur.
    candidate = parse_graph6(candidate_path.read_bytes().strip())
    for high_index, high in enumerate(FIXED):
        for low in FIXED[:high_index]:
            if candidate[low][high] != source[low][high]:
                raise AssertionError("stored candidate does not retain the fixed core")
    candidate_rows = [tuple(candidate[vertex][core] for core in FIXED) for vertex in DESTROY]
    if candidate_rows != sorted(candidate_rows):
        raise AssertionError("stored candidate is not in direct row order")
    candidate_vector = "".join("1" if candidate[low][high] else "0" for low, high in boundary_edges())
    if candidate_vector not in bitset_cases["source_record_12"]["unique_vectors"]:
        raise AssertionError("record-12 candidate vector is absent")

    # Fail-closed corruptions: preserve one manifest record only after proving a
    # one-edge bit flip and a bijective map transposition are both rejected.
    mutated_edge_entry = json.loads(json.dumps(identity_entry))
    vector = mutated_edge_entry["vectors"][0]
    mutated_edge_entry["vectors"][0] = ("1" if vector[0] == "0" else "0") + vector[1:]
    edge_mutation_rejected = False
    try:
        replay_entry(source, source, mutated_edge_entry)
    except AssertionError:
        edge_mutation_rejected = True
    if not edge_mutation_rejected:
        raise AssertionError("one-edge mutation survived replay")

    map_mutation_rejected = False
    rejected_swap: list[int] | None = None
    original_map = list(identity_entry["map_pattern_to_host"])
    for right in range(1, len(original_map)):
        mutated_map_entry = json.loads(json.dumps(identity_entry))
        mutated_map = mutated_map_entry["map_pattern_to_host"]
        mutated_map[0], mutated_map[right] = mutated_map[right], mutated_map[0]
        try:
            replay_entry(source, source, mutated_map_entry)
        except AssertionError:
            map_mutation_rejected = True
            rejected_swap = [0, right]
            break
    if not map_mutation_rejected:
        raise AssertionError("no one-transposition map mutation was rejected")

    # Check every distinct emitted labelled graph using both established exact
    # five-set implementations.  The vector determines the graph because the
    # labelled core is fixed.
    every_vector = sorted({
        vector
        for case_name in ("source_record_21", "source_record_12")
        for vector in bitset_cases[case_name]["unique_vectors"]
    })
    graph6_path = output.with_name("known_class_embedding_pilot_graphs.g6")
    graph6_bytes = b"".join(encode_graph6(reconstruct_labelled(source, vector)) for vector in every_vector)
    graph6_path.write_bytes(graph6_bytes)
    checker_a_result = run_json([sys.executable, str(checker_a), "--format", "graph6", "--input", str(graph6_path)])
    with tempfile.TemporaryDirectory(prefix="r55-embedding-audit-") as temporary:
        executable = Path(temporary) / "checker_b"
        compile_result = subprocess.run(
            ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b), "-o", str(executable)],
            check=True,
            text=True,
            capture_output=True,
            timeout=60,
        )
        if compile_result.stdout or compile_result.stderr:
            raise RuntimeError("unexpected compiler output")
        checker_b_result = run_json([str(executable), "--format", "graph6", "--input", str(graph6_path)])
    graphs_a = checker_a_result["graphs"]
    graphs_b = checker_b_result["graphs"]
    if len(graphs_a) != len(every_vector) or len(graphs_b) != len(every_vector):
        raise AssertionError("checker graph count mismatch")
    for index, (checked_a, checked_b) in enumerate(zip(graphs_a, graphs_b, strict=True)):
        if checked_a["upper_triangle_bits"] != checked_b["upper_triangle_bits"]:
            raise AssertionError("five-set checker parse disagreement")
        if checked_a["zero_k5"] or checked_a["one_k5"] or checked_b["zero_k5"] or checked_b["one_k5"]:
            raise AssertionError("five-set checker found a forbidden set")
        expected_graph = reconstruct_labelled(source, every_vector[index])
        expected_bits = "".join("1" if expected_graph[low][high] else "0" for high in range(1, ORDER) for low in range(high))
        if checked_a["upper_triangle_bits"] != expected_bits:
            raise AssertionError("checker graph differs from manifest vector")

    worst_positive_seconds = max(
        float(bitset_cases[name]["seconds"]) + float(nx_cases[name]["seconds"])
        for name in ("source_record_21", "source_record_12")
    )
    payload = {
        "schema_version": 1,
        "status": "known_class_embedding_two_record_audit_pass",
        "scope": "source records 21 and 12 plus complement-record-21 negative control only",
        "manifest_sha256": {
            "bitset": file_hash(bitset_path),
            "networkx": file_hash(nx_path),
        },
        "exact_stream_comparisons": comparisons,
        "historical_controls": {
            "record_21_identity_embedding_present": True,
            "row_sorted_source_sha256": file_hash(sorted_source_path),
            "record_12_candidate_vector_present": True,
            "record_12_candidate_graph6_sha256": file_hash(candidate_path),
        },
        "adversarial_controls": {
            "one_edge_mutation_rejected": edge_mutation_rejected,
            "one_map_transposition_rejected": map_mutation_rejected,
            "rejected_pattern_index_swap": rejected_swap,
        },
        "dual_five_set_check": {
            "unique_labelled_graphs": len(every_vector),
            "checker_a": checker_a_result["checker"],
            "checker_b": checker_b_result["checker"],
            "all_zero_k5": True,
            "all_one_k5": True,
            "graph6_path": str(graph6_path),
            "graph6_sha256": file_hash(graph6_path),
        },
        "projection": {
            "basis": "worst sum of the two observed positive-host implementation times",
            "worst_observed_seconds_per_host": worst_positive_seconds,
            "projected_656_host_core_hours": worst_positive_seconds * 656 / 3600,
            "qualification": "estimate only; unseen hosts can have more embeddings and tied rows",
        },
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
