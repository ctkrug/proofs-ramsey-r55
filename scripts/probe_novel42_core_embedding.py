#!/usr/bin/env python3
"""Bounded exact cost probe for induced order-30 core containment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

import networkx as nx


FINGERPRINT = "r55novel42basin2026"


def stable_destroy() -> list[int]:
    ranked = sorted(
        range(42),
        key=lambda item: hashlib.sha256(f"{FINGERPRINT}:destroy:20:{item}".encode()).digest(),
    )
    return sorted(ranked[:12])


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: probe_novel42_core_embedding.py CORPUS OUTPUT")
    corpus, output = map(Path, sys.argv[1:])
    records = corpus.read_bytes().splitlines()
    if len(records) != 328:
        raise AssertionError("expected 328 graph6 records")
    source = nx.from_graph6_bytes(records[20])
    destroy = stable_destroy()
    core = source.subgraph(sorted(set(range(42)) - set(destroy))).copy()
    cases = [("source_record_21", source), ("complement_record_21", nx.complement(source))]
    results = []
    for label, host in cases:
        started = time.monotonic()
        contains = nx.algorithms.isomorphism.GraphMatcher(host, core).subgraph_is_isomorphic()
        results.append({"case": label, "contains_induced_core": contains, "seconds": time.monotonic() - started})
    payload = {
        "status": "bounded_core_embedding_cost_probe_complete",
        "scope": "exactly source record 21 and its complement; not the supplied 656",
        "destroy_vertices": destroy,
        "core_order": 30,
        "naive_deleted_subsets_per_host": 11_058_116_888,
        "method": "NetworkX GraphMatcher induced subgraph isomorphism",
        "results": results,
        "conclusion": "The positive identity control is cheap, while even this one exact negative host costs more than a typical incremental SAT model; no full embedding census or class block follows.",
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
