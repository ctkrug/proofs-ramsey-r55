#!/usr/bin/env python3
"""Exact induced-core embedding enumerator using NetworkX VF2.

This implementation intentionally shares no imports with the custom bitset
enumerator.  NetworkX handles both graph6 parsing and induced-isomorphism
enumeration; this script only normalizes and records the complete output.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
import signal
import sys
import time

import networkx as nx


ORDER = 42
DESTROY = [2, 3, 10, 12, 14, 25, 27, 30, 36, 37, 38, 41]
FIXED = sorted(set(range(ORDER)) - set(DESTROY))
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
MAX_VECTORS = 100_000


class EnumerationTimeout(RuntimeError):
    pass


def timeout_handler(_signum: int, _frame: object) -> None:
    raise EnumerationTimeout("VF2 case exceeded its predeclared limit")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stream_digest(lines: list[str]) -> str:
    return digest(b"".join((line + "\n").encode("ascii") for line in lines))


def core_from_source(source: nx.Graph) -> nx.Graph:
    mapping = {old: new for new, old in enumerate(FIXED)}
    return nx.relabel_nodes(source.subgraph(FIXED).copy(), mapping, copy=True)


def upper_bits(graph: nx.Graph) -> str:
    return "".join(
        "1" if graph.has_edge(low, high) else "0"
        for high in range(1, graph.number_of_nodes())
        for low in range(high)
    )


def all_embeddings(host: nx.Graph, pattern: nx.Graph) -> list[tuple[int, ...]]:
    matcher = nx.algorithms.isomorphism.GraphMatcher(host, pattern)
    normalized: list[tuple[int, ...]] = []
    for host_to_pattern in matcher.subgraph_isomorphisms_iter():
        if len(host_to_pattern) != pattern.number_of_nodes():
            raise AssertionError("VF2 returned a partial map")
        pattern_to_host = {pattern_vertex: host_vertex for host_vertex, pattern_vertex in host_to_pattern.items()}
        normalized.append(tuple(pattern_to_host[index] for index in range(pattern.number_of_nodes())))
    normalized.sort()
    if len(normalized) != len(set(normalized)):
        raise AssertionError("VF2 emitted a duplicate normalized embedding")
    return normalized


def expand_boundaries(host: nx.Graph, embeddings: list[tuple[int, ...]]) -> tuple[list[dict[str, object]], list[str]]:
    destroyed = set(DESTROY)
    edges = [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed or high in destroyed
    ]
    if len(edges) != 426:
        raise AssertionError("wrong boundary size")
    records: list[dict[str, object]] = []
    vector_set: set[str] = set()
    total = 0
    for embedding in embeddings:
        residual = sorted(set(host.nodes) - set(embedding))
        row = {
            vertex: tuple(int(host.has_edge(vertex, embedding[position])) for position in range(len(FIXED)))
            for vertex in residual
        }
        grouped: list[list[int]] = []
        ordered_residual = sorted(residual, key=lambda vertex: (row[vertex], vertex))
        for _value, members in itertools.groupby(ordered_residual, key=lambda vertex: row[vertex]):
            grouped.append(list(members))
        multiplicity = math.prod(math.factorial(len(members)) for members in grouped)
        total += multiplicity
        if total > MAX_VECTORS:
            raise RuntimeError("tied-row expansion exceeded the declared cutoff")
        orders: list[list[int]] = []
        vectors: list[str] = []
        within_groups = [list(itertools.permutations(members)) for members in grouped]
        for selected in itertools.product(*within_groups):
            residual_order = [vertex for permutation in selected for vertex in permutation]
            pullback = {label: embedding[position] for position, label in enumerate(FIXED)}
            pullback.update({label: vertex for label, vertex in zip(DESTROY, residual_order, strict=True)})
            bits = "".join(
                "1" if host.has_edge(pullback[low], pullback[high]) else "0"
                for low, high in edges
            )
            orders.append(residual_order)
            vectors.append(bits)
            vector_set.add(bits)
        records.append({
            "map_pattern_to_host": list(embedding),
            "tie_group_sizes": [len(members) for members in grouped],
            "tie_multiplicity": multiplicity,
            "residual_orders": orders,
            "vectors": vectors,
        })
    return records, sorted(vector_set)


def process_case(name: str, pattern: nx.Graph, host: nx.Graph, limit: int) -> dict[str, object]:
    signal.setitimer(signal.ITIMER_REAL, limit)
    start = time.monotonic()
    try:
        embeddings = all_embeddings(host, pattern)
        records, vectors = expand_boundaries(host, embeddings)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    seconds = time.monotonic() - start
    mapping_lines = [",".join(map(str, embedding)) for embedding in embeddings]
    return {
        "case": name,
        "seconds": seconds,
        "embedding_count": len(embeddings),
        "mapping_stream_sha256": stream_digest(mapping_lines),
        "vector_occurrences": sum(int(record["tie_multiplicity"]) for record in records),
        "unique_vector_count": len(vectors),
        "vector_stream_sha256": stream_digest(vectors),
        "embeddings": records,
        "unique_vectors": vectors,
    }


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: enumerate_core_embeddings_networkx.py CORPUS OUTPUT SECONDS")
    corpus_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    limit = int(sys.argv[3])
    corpus_bytes = corpus_path.read_bytes()
    if digest(corpus_bytes) != CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")
    raw_records = corpus_bytes.splitlines()
    if len(raw_records) != 328:
        raise AssertionError("corpus record count mismatch")
    graphs = [nx.from_graph6_bytes(record) for record in raw_records]
    source = graphs[20]
    pattern = core_from_source(source)
    signal.signal(signal.SIGALRM, timeout_handler)
    cases = [
        process_case("source_record_21", pattern, source, limit),
        process_case("source_record_12", pattern, graphs[11], limit),
        process_case("complement_record_21", pattern, nx.complement(source), limit),
    ]
    payload = {
        "schema_version": 1,
        "implementation": "networkx_graph6_vf2_induced",
        "networkx_version": nx.__version__,
        "corpus_sha256": CORPUS_SHA256,
        "core_fixed_labels": FIXED,
        "destroy_labels": DESTROY,
        "core_upper_triangle_sha256": digest(upper_bits(pattern).encode("ascii")),
        "case_limit_seconds": limit,
        "cases": cases,
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "implementation": payload["implementation"],
        "output": str(output_path),
        "cases": [{key: case[key] for key in ("case", "seconds", "embedding_count", "unique_vector_count", "mapping_stream_sha256", "vector_stream_sha256")} for case in cases],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
