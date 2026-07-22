#!/usr/bin/env python3
"""Standalone integrity/coverage validator for the resumed embedding census."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


HOSTS = 656
PREFIX_HOSTS = 254
PREFIX_MANIFEST_SHA256 = "50946975a8be443f08218377924028e6b4762b0a84fd47f10ecb0125e4cfff95"
GATE_SCHEDULE = ((0, 253, 30.0), (254, 655, 60.0))
SUMMARY_KEYS = (
    "embedding_count",
    "mapping_stream_sha256",
    "vector_occurrences",
    "unique_vector_count",
    "vector_stream_sha256",
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def stream_digest(lines: list[str]) -> str:
    return hashlib.sha256(b"".join((line + "\n").encode("ascii") for line in lines)).hexdigest()


def reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(data: str) -> Any:
    return json.loads(
        data,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_constant,
    )


def read_manifest(path: Path) -> tuple[bytes, list[dict[str, Any]], str]:
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    if not raw.endswith(b"\n") or len(lines) != HOSTS:
        raise AssertionError("manifest must contain exactly 656 terminated rows")
    rows: list[dict[str, Any]] = []
    for line in lines:
        if not line.endswith(b"\n") or not line.strip():
            raise AssertionError("manifest contains a blank or unterminated row")
        value = strict_json(line.decode("utf-8"))
        if not isinstance(value, dict):
            raise AssertionError("manifest row is not an object")
        rows.append(value)
    prefix_hash = digest_bytes(b"".join(lines[:PREFIX_HOSTS]))
    return raw, rows, prefix_hash


def expected_case(index: int) -> str:
    source_index = index % 328
    kind = "complement" if index >= 328 else "source"
    return f"{kind}_record_{source_index + 1}"


def expected_gate(index: int) -> float:
    return 30.0 if index < PREFIX_HOSTS else 60.0


def finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssertionError(f"{label} is not numeric")
    result = float(value)
    if not math.isfinite(result):
        raise AssertionError(f"{label} is not finite")
    return result


def safe_artifact(manifest: Path, relative: Any) -> Path:
    if not isinstance(relative, str):
        raise AssertionError("artifact path is not a string")
    candidate = Path(relative)
    if candidate.is_absolute():
        raise AssertionError("absolute artifact path is forbidden")
    root = manifest.parent.resolve()
    resolved = (manifest.parent / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise AssertionError("artifact path escapes manifest output directory") from error
    if not resolved.is_file() or (manifest.parent / candidate).is_symlink():
        raise AssertionError(f"artifact is absent, non-regular, or a symlink: {relative}")
    return resolved


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def validate(
    manifest: Path,
    *,
    expected_prefix_sha256: str = PREFIX_MANIFEST_SHA256,
) -> dict[str, Any]:
    raw, rows, prefix_hash = read_manifest(manifest)
    if prefix_hash != expected_prefix_sha256:
        raise AssertionError("resumed manifest does not preserve the frozen 254-row prefix bytes")
    if [row.get("host_index") for row in rows] != list(range(HOSTS)):
        raise AssertionError("manifest does not cover each of 656 hosts exactly once in canonical order")

    max_host_seconds = {30.0: 0.0, 60.0: 0.0}
    for index, row in enumerate(rows):
        if row.get("case") != expected_case(index):
            raise AssertionError(f"case name mismatch: {index}")
        host_seconds = finite_number(row.get("host_seconds"), f"host {index} elapsed")
        host_gate = finite_number(row.get("host_gate_seconds"), f"host {index} gate")
        bitset_seconds = finite_number(row.get("bitset_seconds"), f"host {index} bitset elapsed")
        networkx_seconds = finite_number(row.get("networkx_seconds"), f"host {index} NetworkX elapsed")
        gate = expected_gate(index)
        if (
            host_gate != gate
            or not 0 < bitset_seconds <= host_seconds
            or not 0 < networkx_seconds <= host_seconds
            or bitset_seconds + networkx_seconds > host_seconds
            or host_seconds > host_gate
        ):
            raise AssertionError(f"invalid mixed aggregate host gate receipt: {index}")
        max_host_seconds[gate] = max(max_host_seconds[gate], host_seconds)

        artifact = safe_artifact(manifest, row.get("artifact"))
        if digest(artifact) != row.get("artifact_sha256"):
            raise AssertionError(f"artifact hash mismatch: {index}")
        with gzip.open(artifact, "rt", encoding="utf-8") as handle:
            payload = strict_json(handle.read())
        if not isinstance(payload, dict):
            raise AssertionError(f"artifact payload is not an object: {index}")
        left, right = payload.get("bitset"), payload.get("networkx_summary")
        if not isinstance(left, dict) or not isinstance(right, dict):
            raise AssertionError(f"artifact summaries are malformed: {index}")
        if left.get("case") != row["case"]:
            raise AssertionError(f"artifact case mismatch: {index}")
        if any(left.get(key) != row.get(key) or right.get(key) != row.get(key) for key in SUMMARY_KEYS):
            raise AssertionError(f"summary mismatch: {index}")
        vectors = left.get("unique_vectors")
        if not isinstance(vectors, list) or any(not isinstance(vector, str) for vector in vectors):
            raise AssertionError(f"vector stream is malformed: {index}")
        if stream_digest(vectors) != row.get("vector_stream_sha256"):
            raise AssertionError(f"vector stream mismatch: {index}")

    return {
        "schema_version": 2,
        "status": "valid",
        "hosts": len(rows),
        "manifest_sha256": digest_bytes(raw),
        "original_prefix_hosts": PREFIX_HOSTS,
        "original_prefix_manifest_sha256": prefix_hash,
        "aggregate_host_gate_schedule": [
            {"first_host": first, "last_host": last, "seconds": seconds}
            for first, last, seconds in GATE_SCHEDULE
        ],
        "max_observed_host_seconds": {
            "cap_30_prefix": max_host_seconds[30.0],
            "cap_60_continuation": max_host_seconds[60.0],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.manifest)
    if args.output:
        atomic_json(args.output, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
