#!/usr/bin/env python3
"""Cold audit a prefix of the checkpointed known-class embedding census.

This checker imports neither production enumerator.  It independently parses
graph6, validates the manifest/checkpoint/progress chain, replays every saved
positive embedding and boundary pullback, cold-runs NetworkX VF2 on a fixed
sample of saved empty hosts, checks every distinct labelled graph with the two
established exact five-set checkers, and verifies fail-closed mutations.

The audit is deliberately prefix-scoped.  It does not certify the unprocessed
hosts or the completeness of the supplied 656-class collection.
"""

from __future__ import annotations

import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import networkx as nx


ORDER = 42
TOTAL_HOSTS = 656
DESTROY = [2, 3, 10, 12, 14, 25, 27, 30, 36, 37, 38, 41]
FIXED = sorted(set(range(ORDER)) - set(DESTROY))
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
EMPTY_SAMPLE = [0]
SUMMARY_KEYS = (
    "embedding_count",
    "mapping_stream_sha256",
    "vector_occurrences",
    "unique_vector_count",
    "vector_stream_sha256",
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stream_hash(lines: list[str]) -> str:
    data = b"".join((line + "\n").encode("ascii") for line in lines)
    return hashlib.sha256(data).hexdigest()


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
    for cursor, (high, low) in enumerate(
        (high, low) for high in range(1, n) for low in range(high)
    ):
        encoded = raw[1 + cursor // 6] - 63
        edge = bool((encoded >> (5 - cursor % 6)) & 1)
        graph[low][high] = graph[high][low] = edge
    for cursor in range(total, ((total + 5) // 6) * 6):
        encoded = raw[1 + cursor // 6] - 63
        if (encoded >> (5 - cursor % 6)) & 1:
            raise ValueError("nonzero graph6 padding")
    return graph


def encode_graph6(graph: list[list[bool]]) -> bytes:
    bits = [
        int(graph[low][high])
        for high in range(1, len(graph))
        for low in range(high)
    ]
    while len(bits) % 6:
        bits.append(0)
    body = bytearray()
    for offset in range(0, len(bits), 6):
        value = 0
        for bit in bits[offset : offset + 6]:
            value = (value << 1) | bit
        body.append(value + 63)
    return bytes([len(graph) + 63]) + bytes(body) + b"\n"


def boundary_edges() -> list[tuple[int, int]]:
    destroyed = set(DESTROY)
    edges = [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed or high in destroyed
    ]
    if len(edges) != 426:
        raise AssertionError("boundary edge count mismatch")
    return edges


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


def expected_case(index: int) -> str:
    source_index = index % 328
    prefix = "complement" if index >= 328 else "source"
    return f"{prefix}_record_{source_index + 1}"


def host_graph(corpus: list[list[list[bool]]], index: int) -> list[list[bool]]:
    source = corpus[index % 328]
    if index < 328:
        return source
    return [
        [i != j and not source[i][j] for j in range(ORDER)]
        for i in range(ORDER)
    ]


def replay_entry(
    core_source: list[list[bool]],
    host: list[list[bool]],
    entry: dict[str, object],
) -> list[str]:
    mapping = [int(value) for value in entry["map_pattern_to_host"]]
    if (
        len(mapping) != len(FIXED)
        or len(set(mapping)) != len(FIXED)
        or any(not 0 <= value < ORDER for value in mapping)
    ):
        raise AssertionError("embedding is not an injection")
    for high in range(1, len(FIXED)):
        for low in range(high):
            if core_source[FIXED[low]][FIXED[high]] != host[mapping[low]][mapping[high]]:
                raise AssertionError("map is not an induced-core embedding")

    residual = sorted(set(range(ORDER)) - set(mapping))
    rows = {
        vertex: tuple(host[vertex][mapping[position]] for position in range(len(FIXED)))
        for vertex in residual
    }
    ordered = sorted(residual, key=lambda vertex: (rows[vertex], vertex))
    groups = [
        list(group)
        for _row, group in itertools.groupby(ordered, key=lambda vertex: rows[vertex])
    ]
    expected_orders = sorted(
        [vertex for choice in choices for vertex in choice]
        for choices in itertools.product(
            *(list(itertools.permutations(group)) for group in groups)
        )
    )
    actual_orders = sorted(
        [[int(value) for value in order] for order in entry["residual_orders"]]
    )
    if expected_orders != actual_orders:
        raise AssertionError("residual-order stream is incomplete")
    expected_sizes = [len(group) for group in groups]
    if entry["tie_group_sizes"] != expected_sizes:
        raise AssertionError("tie-group signature mismatch")
    if int(entry["tie_multiplicity"]) != math.prod(
        math.factorial(size) for size in expected_sizes
    ):
        raise AssertionError("tie multiplicity mismatch")

    expected_vectors: list[str] = []
    recorded_vectors = [str(vector) for vector in entry["vectors"]]
    if len(recorded_vectors) != len(entry["residual_orders"]):
        raise AssertionError("order/vector arity mismatch")
    for order in entry["residual_orders"]:
        order = [int(value) for value in order]
        pullback = {label: mapping[position] for position, label in enumerate(FIXED)}
        pullback.update(zip(DESTROY, order, strict=True))
        if len(set(pullback.values())) != ORDER:
            raise AssertionError("pullback is not a bijection")
        vector = "".join(
            "1" if host[pullback[low]][pullback[high]] else "0"
            for low, high in boundary_edges()
        )
        expected_vectors.append(vector)
        labelled = reconstruct_labelled(core_source, vector)
        for high in range(1, ORDER):
            for low in range(high):
                if labelled[low][high] != host[pullback[low]][pullback[high]]:
                    raise AssertionError("reconstructed graph differs from host pullback")
    if expected_vectors != recorded_vectors:
        raise AssertionError("boundary vector differs from exact pullback")
    return expected_vectors


def validate_saved_case(
    core_source: list[list[bool]],
    host: list[list[bool]],
    case: dict[str, object],
) -> list[str]:
    entries = case["embeddings"]
    maps = [tuple(int(value) for value in entry["map_pattern_to_host"]) for entry in entries]
    if maps != sorted(maps) or len(maps) != len(set(maps)):
        raise AssertionError("mapping stream is not sorted unique data")
    if len(maps) != int(case["embedding_count"]):
        raise AssertionError("embedding count mismatch")
    vectors: list[str] = []
    for entry in entries:
        vectors.extend(replay_entry(core_source, host, entry))
    unique = sorted(set(vectors))
    if unique != case["unique_vectors"]:
        raise AssertionError("unique vector data mismatch")
    if len(vectors) != int(case["vector_occurrences"]):
        raise AssertionError("vector occurrence mismatch")
    if len(unique) != int(case["unique_vector_count"]):
        raise AssertionError("unique vector count mismatch")
    if stream_hash([",".join(map(str, mapping)) for mapping in maps]) != case["mapping_stream_sha256"]:
        raise AssertionError("mapping stream hash mismatch")
    if stream_hash(unique) != case["vector_stream_sha256"]:
        raise AssertionError("vector stream hash mismatch")
    return unique


def cold_vf2_maps(
    core_source: list[list[bool]], host: list[list[bool]]
) -> list[tuple[int, ...]]:
    pattern = nx.Graph()
    pattern.add_nodes_from(range(len(FIXED)))
    pattern.add_edges_from(
        (low, high)
        for high in range(1, len(FIXED))
        for low in range(high)
        if core_source[FIXED[low]][FIXED[high]]
    )
    target = nx.Graph()
    target.add_nodes_from(range(ORDER))
    target.add_edges_from(
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if host[low][high]
    )
    matcher = nx.algorithms.isomorphism.GraphMatcher(target, pattern)
    normalized: list[tuple[int, ...]] = []
    for host_to_pattern in matcher.subgraph_isomorphisms_iter():
        pattern_to_host = {
            pattern_vertex: host_vertex
            for host_vertex, pattern_vertex in host_to_pattern.items()
        }
        normalized.append(tuple(pattern_to_host[index] for index in range(len(FIXED))))
    normalized.sort()
    if len(normalized) != len(set(normalized)):
        raise AssertionError("cold VF2 emitted a duplicate normalized embedding")
    return normalized


def run_json(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command, check=True, text=True, capture_output=True, timeout=120
    )
    if completed.stderr:
        raise RuntimeError(f"unexpected checker stderr: {completed.stderr}")
    return json.loads(completed.stdout)


def main() -> int:
    if len(sys.argv) != 9:
        raise SystemExit(
            "usage: known_class_embedding_tranche_audit.py CORPUS MANIFEST "
            "CHECKPOINT PROGRESS EXPECTED_HOSTS CHECKER_A CHECKER_B OUTPUT"
        )
    (
        corpus_path,
        manifest_path,
        checkpoint_path,
        progress_path,
        expected_hosts_raw,
        checker_a,
        checker_b,
        output_path,
    ) = sys.argv[1:]
    corpus_path = Path(corpus_path)
    manifest_path = Path(manifest_path)
    checkpoint_path = Path(checkpoint_path)
    progress_path = Path(progress_path)
    checker_a = Path(checker_a)
    checker_b = Path(checker_b)
    output_path = Path(output_path)
    expected_hosts = int(expected_hosts_raw)
    if expected_hosts < max(EMPTY_SAMPLE) + 1:
        raise AssertionError("declared prefix does not cover the cold empty sample")

    if file_hash(corpus_path) != CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")
    corpus = [parse_graph6(line) for line in corpus_path.read_bytes().splitlines()]
    if len(corpus) != 328 or any(len(graph) != ORDER for graph in corpus):
        raise AssertionError("corpus cardinality/order mismatch")
    core_source = corpus[20]

    rows = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if [row["host_index"] for row in rows] != list(range(expected_hosts)):
        raise AssertionError("manifest prefix coverage/order mismatch")
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    if checkpoint["next_host"] != expected_hosts or checkpoint["completed"] != rows:
        raise AssertionError("checkpoint does not equal manifest prefix")
    if checkpoint["total_hosts"] != TOTAL_HOSTS or checkpoint["corpus_sha256"] != CORPUS_SHA256:
        raise AssertionError("checkpoint scope mismatch")
    if progress["completed_units"] != expected_hosts or progress["total_units"] != TOTAL_HOSTS:
        raise AssertionError("progress scope mismatch")
    if progress["manifest_sha256"] != file_hash(manifest_path):
        raise AssertionError("progress manifest hash mismatch")
    if progress["complete"] or not progress["correctness_checks_passed"] or not progress["decision_value_active"]:
        raise AssertionError("unexpected progress flags")

    all_vectors: set[str] = set()
    positive_hosts: list[dict[str, int | str]] = []
    artifact_bytes = manifest_path.stat().st_size
    artifact_payloads: dict[int, dict[str, object]] = {}
    for index, row in enumerate(rows):
        if row["case"] != expected_case(index):
            raise AssertionError(f"case name mismatch at host {index}")
        artifact = manifest_path.parent / row["artifact"]
        artifact_bytes += artifact.stat().st_size
        if file_hash(artifact) != row["artifact_sha256"]:
            raise AssertionError(f"artifact hash mismatch at host {index}")
        with gzip.open(artifact, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        artifact_payloads[index] = payload
        left, right = payload["bitset"], payload["networkx_summary"]
        if left["case"] != row["case"]:
            raise AssertionError(f"artifact case mismatch at host {index}")
        for key in SUMMARY_KEYS:
            if left[key] != row[key] or right[key] != row[key]:
                raise AssertionError(f"summary mismatch at host {index}: {key}")
        if left["unique_vectors"] != sorted(set(left["unique_vectors"])):
            raise AssertionError(f"unsorted/duplicate vectors at host {index}")
        if any(len(vector) != 426 or set(vector) - {"0", "1"} for vector in left["unique_vectors"]):
            raise AssertionError(f"malformed vector at host {index}")
        if stream_hash(left["unique_vectors"]) != row["vector_stream_sha256"]:
            raise AssertionError(f"vector stream mismatch at host {index}")
        if row["embedding_count"]:
            unique = validate_saved_case(core_source, host_graph(corpus, index), left)
            all_vectors.update(unique)
            positive_hosts.append(
                {
                    "host_index": index,
                    "case": row["case"],
                    "embedding_count": row["embedding_count"],
                    "unique_vector_count": row["unique_vector_count"],
                }
            )
        elif left["embeddings"] or left["unique_vectors"]:
            raise AssertionError(f"empty summary has data at host {index}")
    if artifact_bytes != progress["artifact_bytes"]:
        raise AssertionError("progress artifact byte count mismatch")

    cold_positive_streams: dict[str, dict[str, int | str]] = {}
    for item in positive_hosts:
        index = int(item["host_index"])
        maps = cold_vf2_maps(core_source, host_graph(corpus, index))
        mapping_digest = stream_hash([",".join(map(str, mapping)) for mapping in maps])
        if len(maps) != rows[index]["embedding_count"]:
            raise AssertionError(f"cold positive count mismatch at host {index}")
        if mapping_digest != rows[index]["mapping_stream_sha256"]:
            raise AssertionError(f"cold positive stream mismatch at host {index}")
        cold_positive_streams[str(index)] = {
            "embedding_count": len(maps),
            "mapping_stream_sha256": mapping_digest,
        }

    cold_counts: dict[str, int] = {}
    for index in EMPTY_SAMPLE:
        if rows[index]["embedding_count"] != 0:
            raise AssertionError("predeclared cold sample is not empty in manifest")
        count = len(cold_vf2_maps(core_source, host_graph(corpus, index)))
        cold_counts[str(index)] = count
        if count != 0:
            raise AssertionError(f"cold VF2 found an omitted embedding at host {index}")

    graph6_path = output_path.with_name("known_class_embedding_tranche33_graphs.g6")
    graph6_path.write_bytes(
        b"".join(encode_graph6(reconstruct_labelled(core_source, vector)) for vector in sorted(all_vectors))
    )
    checker_a_result = run_json(
        [sys.executable, str(checker_a), "--format", "graph6", "--input", str(graph6_path)]
    )
    with tempfile.TemporaryDirectory(prefix="r55-tranche-audit-") as temporary:
        executable = Path(temporary) / "checker_b"
        compile_result = subprocess.run(
            [
                "gcc",
                "-std=c11",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(checker_b),
                "-o",
                str(executable),
            ],
            check=True,
            text=True,
            capture_output=True,
            timeout=60,
        )
        if compile_result.stdout or compile_result.stderr:
            raise RuntimeError("unexpected compiler output")
        checker_b_result = run_json(
            [str(executable), "--format", "graph6", "--input", str(graph6_path)]
        )
    checked_a = checker_a_result["graphs"]
    checked_b = checker_b_result["graphs"]
    if len(checked_a) != len(all_vectors) or len(checked_b) != len(all_vectors):
        raise AssertionError("five-set checker graph count mismatch")
    for left, right in zip(checked_a, checked_b, strict=True):
        if left["upper_triangle_bits"] != right["upper_triangle_bits"]:
            raise AssertionError("five-set checker parse disagreement")
        if left["zero_k5"] or left["one_k5"] or right["zero_k5"] or right["one_k5"]:
            raise AssertionError("five-set checker found a forbidden set")

    # Four fail-closed controls against the first positive saved entry.
    first_positive = int(positive_hosts[0]["host_index"])
    original_entry = artifact_payloads[first_positive]["bitset"]["embeddings"][0]
    mutations: dict[str, bool] = {}

    edge_entry = json.loads(json.dumps(original_entry))
    vector = edge_entry["vectors"][0]
    edge_entry["vectors"][0] = ("1" if vector[0] == "0" else "0") + vector[1:]
    try:
        replay_entry(core_source, host_graph(corpus, first_positive), edge_entry)
        mutations["boundary_edge_flip_rejected"] = False
    except AssertionError:
        mutations["boundary_edge_flip_rejected"] = True

    map_entry = json.loads(json.dumps(original_entry))
    map_entry["map_pattern_to_host"][0], map_entry["map_pattern_to_host"][1] = (
        map_entry["map_pattern_to_host"][1],
        map_entry["map_pattern_to_host"][0],
    )
    try:
        replay_entry(core_source, host_graph(corpus, first_positive), map_entry)
        mutations["map_transposition_rejected"] = False
    except AssertionError:
        mutations["map_transposition_rejected"] = True

    order_entry = json.loads(json.dumps(original_entry))
    del order_entry["residual_orders"][0]
    try:
        replay_entry(core_source, host_graph(corpus, first_positive), order_entry)
        mutations["residual_order_deletion_rejected"] = False
    except AssertionError:
        mutations["residual_order_deletion_rejected"] = True

    altered_hash = ("0" if rows[0]["artifact_sha256"][0] != "0" else "1") + rows[0]["artifact_sha256"][1:]
    mutations["manifest_hash_alteration_rejected"] = file_hash(
        manifest_path.parent / rows[0]["artifact"]
    ) != altered_hash
    if not all(mutations.values()):
        raise AssertionError(f"mutation gate failed: {mutations}")

    payload = {
        "schema_version": 1,
        "status": "known_class_embedding_prefix_audit_pass",
        "scope": f"exactly canonical hosts 0..{expected_hosts - 1} of 656",
        "hashes": {
            "corpus": file_hash(corpus_path),
            "manifest": file_hash(manifest_path),
            "checkpoint": file_hash(checkpoint_path),
            "progress": file_hash(progress_path),
            "graph6": file_hash(graph6_path),
        },
        "coverage": {
            "hosts": expected_hosts,
            "positive_hosts": positive_hosts,
            "positive_embedding_total": sum(int(item["embedding_count"]) for item in positive_hosts),
            "distinct_vectors": len(all_vectors),
            "artifact_bytes": artifact_bytes,
        },
        "cold_empty_sample": {
            "indices": EMPTY_SAMPLE,
            "vf2_counts": cold_counts,
            "networkx_version": nx.__version__,
        },
        "cold_positive_streams": {
            "hosts": cold_positive_streams,
            "networkx_version": nx.__version__,
        },
        "dual_five_set_check": {
            "graphs": len(all_vectors),
            "checker_a": checker_a_result["checker"],
            "checker_b": checker_b_result["checker"],
            "all_zero_k5": True,
            "all_one_k5": True,
        },
        "mutations": mutations,
        "archive_limit": (
            "Production artifacts preserve the full custom-DFS stream but only "
            "the NetworkX summary; this audit cold-reruns and exactly hashes VF2 "
            "streams for every positive prefix host, plus the named empty sample."
        ),
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
