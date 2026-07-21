#!/usr/bin/env python3
"""Exact induced-core embedding enumerator using a custom bitset DFS.

This implementation intentionally does not import NetworkX or the companion
VF2 implementation.  Its output is a deterministic, replayable JSON manifest.
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


ORDER = 42
SOURCE_RECORD = 21
DESTROY = [2, 3, 10, 12, 14, 25, 27, 30, 36, 37, 38, 41]
FIXED = sorted(set(range(ORDER)) - set(DESTROY))
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
MAX_VECTORS = 100_000


class CaseTimeout(RuntimeError):
    pass


def alarm_handler(_signum: int, _frame: object) -> None:
    raise CaseTimeout("case exceeded the predeclared time limit")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_stream(lines: list[str]) -> str:
    return sha256_bytes(b"".join((line + "\n").encode("ascii") for line in lines))


def decode_short_graph6(raw: bytes) -> list[int]:
    if not raw or any(byte < 63 or byte > 126 for byte in raw):
        raise ValueError("invalid graph6 record")
    n = raw[0] - 63
    if not 1 <= n <= 62:
        raise ValueError("only short graph6 records are supported")
    edge_bits = n * (n - 1) // 2
    if len(raw) != 1 + (edge_bits + 5) // 6:
        raise ValueError("graph6 record length mismatch")
    masks = [0] * n
    cursor = 0
    for high in range(1, n):
        for low in range(high):
            value = raw[1 + cursor // 6] - 63
            if (value >> (5 - cursor % 6)) & 1:
                masks[low] |= 1 << high
                masks[high] |= 1 << low
            cursor += 1
    for bit in range(cursor, ((edge_bits + 5) // 6) * 6):
        value = raw[1 + bit // 6] - 63
        if (value >> (5 - bit % 6)) & 1:
            raise ValueError("nonzero graph6 padding")
    return masks


def complement(masks: list[int]) -> list[int]:
    all_vertices = (1 << len(masks)) - 1
    return [all_vertices & ~(1 << vertex) & ~mask for vertex, mask in enumerate(masks)]


def induced_pattern(source: list[int]) -> list[int]:
    index = {old: new for new, old in enumerate(FIXED)}
    result = [0] * len(FIXED)
    for new_u, old_u in enumerate(FIXED):
        for old_v in FIXED:
            if (source[old_u] >> old_v) & 1:
                result[new_u] |= 1 << index[old_v]
    return result


def adjacency_bits(masks: list[int]) -> str:
    return "".join(
        "1" if (masks[low] >> high) & 1 else "0"
        for high in range(1, len(masks))
        for low in range(high)
    )


def enumerate_embeddings(pattern: list[int], host: list[int]) -> tuple[list[tuple[int, ...]], dict[str, int]]:
    pn, hn = len(pattern), len(host)
    all_host = (1 << hn) - 1
    all_pattern = (1 << pn) - 1
    pdegrees = [mask.bit_count() for mask in pattern]
    hdegrees = [mask.bit_count() for mask in host]
    base: list[int] = []
    for p in range(pn):
        domain = 0
        for h in range(hn):
            if pdegrees[p] <= hdegrees[h] and pn - 1 - pdegrees[p] <= hn - 1 - hdegrees[h]:
                domain |= 1 << h
        base.append(domain)

    mapping = [-1] * pn
    solutions: list[tuple[int, ...]] = []
    stats = {"search_nodes": 0, "forward_prunes": 0, "hall_union_prunes": 0}

    def domain_for(p: int, unused_h: int, unmapped_p: int) -> int:
        candidates = base[p] & unused_h
        for q, hq in enumerate(mapping):
            if hq < 0:
                continue
            if (pattern[p] >> q) & 1:
                candidates &= host[hq]
            else:
                candidates &= all_host & ~host[hq] & ~(1 << hq)
        remaining_pattern = unmapped_p & ~(1 << p)
        need_neighbors = (pattern[p] & remaining_pattern).bit_count()
        need_nonneighbors = remaining_pattern.bit_count() - need_neighbors
        filtered = 0
        scan = candidates
        while scan:
            hbit = scan & -scan
            h = hbit.bit_length() - 1
            remaining_host = unused_h & ~hbit
            have_neighbors = (host[h] & remaining_host).bit_count()
            have_nonneighbors = remaining_host.bit_count() - have_neighbors
            if have_neighbors >= need_neighbors and have_nonneighbors >= need_nonneighbors:
                filtered |= hbit
            scan ^= hbit
        return filtered

    def dfs(unused_h: int, unmapped_p: int) -> None:
        stats["search_nodes"] += 1
        if not unmapped_p:
            solutions.append(tuple(mapping))
            return

        chosen = -1
        chosen_domain = 0
        chosen_key: tuple[int, int, int] | None = None
        union = 0
        remaining = unmapped_p
        while remaining:
            pbit = remaining & -remaining
            p = pbit.bit_length() - 1
            domain = domain_for(p, unused_h, unmapped_p)
            size = domain.bit_count()
            if not size:
                stats["forward_prunes"] += 1
                return
            union |= domain
            mapped_neighbors = (pattern[p] & (all_pattern ^ unmapped_p)).bit_count()
            key = (size, -mapped_neighbors, -pdegrees[p])
            if chosen_key is None or key < chosen_key:
                chosen, chosen_domain, chosen_key = p, domain, key
            remaining ^= pbit
        if union.bit_count() < unmapped_p.bit_count():
            stats["hall_union_prunes"] += 1
            return

        scan = chosen_domain
        while scan:
            hbit = scan & -scan
            h = hbit.bit_length() - 1
            mapping[chosen] = h
            dfs(unused_h ^ hbit, unmapped_p ^ (1 << chosen))
            mapping[chosen] = -1
            scan ^= hbit

    dfs(all_host, all_pattern)
    solutions.sort()
    if len(solutions) != len(set(solutions)):
        raise AssertionError("duplicate embedding emitted")
    return solutions, stats


def boundary_records(host: list[int], embeddings: list[tuple[int, ...]]) -> tuple[list[dict[str, object]], list[str]]:
    destroyed_set = set(DESTROY)
    boundary_edges = [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed_set or high in destroyed_set
    ]
    if len(boundary_edges) != 426:
        raise AssertionError("boundary edge count mismatch")
    entries: list[dict[str, object]] = []
    unique: set[str] = set()
    expansion_total = 0
    for embedding in embeddings:
        image = set(embedding)
        residual = sorted(set(range(ORDER)) - image)
        rows = {
            vertex: tuple((host[vertex] >> embedding[index]) & 1 for index in range(len(FIXED)))
            for vertex in residual
        }
        groups: list[list[int]] = []
        for _row, group in itertools.groupby(sorted(residual, key=lambda vertex: (rows[vertex], vertex)), key=lambda vertex: rows[vertex]):
            groups.append(list(group))
        multiplicity = math.prod(math.factorial(len(group)) for group in groups)
        expansion_total += multiplicity
        if expansion_total > MAX_VECTORS:
            raise RuntimeError("tied-row expansion exceeded 100000 vectors")
        orders: list[list[int]] = []
        vectors: list[str] = []
        group_permutations = [list(itertools.permutations(group)) for group in groups]
        for choices in itertools.product(*group_permutations):
            order = [vertex for choice in choices for vertex in choice]
            label_to_host = {fixed: embedding[index] for index, fixed in enumerate(FIXED)}
            label_to_host.update(zip(DESTROY, order, strict=True))
            vector = "".join(
                "1" if (host[label_to_host[low]] >> label_to_host[high]) & 1 else "0"
                for low, high in boundary_edges
            )
            orders.append(order)
            vectors.append(vector)
            unique.add(vector)
        entries.append({
            "map_pattern_to_host": list(embedding),
            "tie_group_sizes": [len(group) for group in groups],
            "tie_multiplicity": multiplicity,
            "residual_orders": orders,
            "vectors": vectors,
        })
    return entries, sorted(unique)


def run_case(name: str, pattern: list[int], host: list[int], seconds: int) -> dict[str, object]:
    signal.setitimer(signal.ITIMER_REAL, seconds)
    started = time.monotonic()
    try:
        embeddings, stats = enumerate_embeddings(pattern, host)
        entries, vectors = boundary_records(host, embeddings)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    elapsed = time.monotonic() - started
    mapping_lines = [",".join(map(str, embedding)) for embedding in embeddings]
    return {
        "case": name,
        "seconds": elapsed,
        "embedding_count": len(embeddings),
        "mapping_stream_sha256": sha256_stream(mapping_lines),
        "vector_occurrences": sum(int(entry["tie_multiplicity"]) for entry in entries),
        "unique_vector_count": len(vectors),
        "vector_stream_sha256": sha256_stream(vectors),
        "embeddings": entries,
        "unique_vectors": vectors,
        "search_stats": stats,
    }


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: enumerate_core_embeddings_bitset.py CORPUS OUTPUT SECONDS")
    corpus_path, output_path = map(Path, sys.argv[1:3])
    limit = int(sys.argv[3])
    raw_corpus = corpus_path.read_bytes()
    if sha256_bytes(raw_corpus) != CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")
    records = raw_corpus.splitlines()
    if len(records) != 328:
        raise AssertionError("corpus record count mismatch")
    graphs = [decode_short_graph6(record) for record in records]
    source = graphs[SOURCE_RECORD - 1]
    pattern = induced_pattern(source)
    signal.signal(signal.SIGALRM, alarm_handler)
    cases = [
        run_case("source_record_21", pattern, source, limit),
        run_case("source_record_12", pattern, graphs[11], limit),
        run_case("complement_record_21", pattern, complement(source), limit),
    ]
    payload = {
        "schema_version": 1,
        "implementation": "custom_graph6_bitset_dfs",
        "corpus_sha256": CORPUS_SHA256,
        "core_fixed_labels": FIXED,
        "destroy_labels": DESTROY,
        "core_upper_triangle_sha256": sha256_bytes(adjacency_bits(pattern).encode("ascii")),
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
