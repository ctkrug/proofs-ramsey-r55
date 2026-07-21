#!/usr/bin/env python3
"""Standalone integrity/coverage validator for a complete embedding census."""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def stream_digest(lines: list[str]) -> str:
    return hashlib.sha256(b"".join((line + "\n").encode("ascii") for line in lines)).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_known_class_embedding_census.py MANIFEST.jsonl")
    manifest = Path(sys.argv[1])
    rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
    expected = list(range(656))
    if [row["host_index"] for row in rows] != expected:
        raise AssertionError("manifest does not cover each of 656 hosts exactly once in canonical order")
    keys = ("embedding_count", "mapping_stream_sha256", "vector_occurrences", "unique_vector_count", "vector_stream_sha256")
    for row in rows:
        artifact = Path(row["artifact"])
        if not artifact.is_absolute():
            artifact = manifest.parent / artifact
        if digest(artifact) != row["artifact_sha256"]:
            raise AssertionError(f"artifact hash mismatch: {row['host_index']}")
        with gzip.open(artifact, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        left, right = payload["bitset"], payload["networkx_summary"]
        if any(left[key] != row[key] or right[key] != row[key] for key in keys):
            raise AssertionError(f"summary mismatch: {row['host_index']}")
        if stream_digest(left["unique_vectors"]) != row["vector_stream_sha256"]:
            raise AssertionError(f"vector stream mismatch: {row['host_index']}")
    print(json.dumps({"status": "valid", "hosts": len(rows), "manifest_sha256": digest(manifest)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
