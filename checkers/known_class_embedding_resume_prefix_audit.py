#!/usr/bin/env python3
"""Verify an exact copy of the stopped 254-host census prefix.

This checker deliberately binds the byte representation of the original manifest,
not merely its decoded JSON values.  It is intended to run after the manifest,
checkpoint, and host artifacts are copied into a fresh experiment directory and
before that directory is admitted for continuation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


PREFIX_HOSTS = 254
TOTAL_HOSTS = 656
HOST_GATE_SECONDS = 30.0
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
ORIGINAL_MANIFEST_SHA256 = "50946975a8be443f08218377924028e6b4762b0a84fd47f10ecb0125e4cfff95"
ORIGINAL_CHECKPOINT_SHA256 = "12dd99da2e5f122954b08806376e6449ee779ad670855a7328b4c5f3ff1d2332"


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


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


def manifest_rows(path: Path) -> tuple[bytes, list[dict[str, Any]]]:
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    if not raw.endswith(b"\n") or len(lines) != PREFIX_HOSTS:
        raise AssertionError("manifest is not the exact 254-line stopped prefix")
    rows: list[dict[str, Any]] = []
    for line in lines:
        if not line.endswith(b"\n") or not line.strip():
            raise AssertionError("manifest contains a blank or unterminated row")
        value = strict_json(line.decode("utf-8"))
        if not isinstance(value, dict):
            raise AssertionError("manifest row is not an object")
        rows.append(value)
    return raw, rows


def expected_case(index: int) -> str:
    source_index = index % 328
    kind = "complement" if index >= 328 else "source"
    return f"{kind}_record_{source_index + 1}"


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
        raise AssertionError("artifact path escapes the copied output") from error
    if not resolved.is_file() or (manifest.parent / candidate).is_symlink():
        raise AssertionError(f"artifact is absent, non-regular, or a symlink: {relative}")
    return resolved


def validate_rows(manifest: Path, rows: list[dict[str, Any]]) -> str:
    if [row.get("host_index") for row in rows] != list(range(PREFIX_HOSTS)):
        raise AssertionError("manifest is not the canonical host prefix 0..253")
    artifact_hashes = hashlib.sha256()
    for index, row in enumerate(rows):
        if row.get("case") != expected_case(index):
            raise AssertionError(f"case name mismatch at host {index}")
        gate = finite_number(row.get("host_gate_seconds"), f"host {index} gate")
        elapsed = finite_number(row.get("host_seconds"), f"host {index} elapsed")
        if gate != HOST_GATE_SECONDS or not 0 < elapsed <= gate:
            raise AssertionError(f"invalid original host gate receipt at host {index}")
        expected_hash = row.get("artifact_sha256")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise AssertionError(f"invalid artifact hash at host {index}")
        artifact = safe_artifact(manifest, row.get("artifact"))
        if digest(artifact) != expected_hash:
            raise AssertionError(f"artifact hash mismatch at host {index}")
        artifact_hashes.update(f"{index}:{expected_hash}\n".encode("ascii"))
    return artifact_hashes.hexdigest()


def validate_checkpoint(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    value = strict_json(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("checkpoint is not an object")
    if value != {
        "completed": rows,
        "corpus_sha256": CORPUS_SHA256,
        "next_host": PREFIX_HOSTS,
        "schema_version": 1,
        "total_hosts": TOTAL_HOSTS,
    }:
        raise AssertionError("checkpoint is not exactly the stopped manifest state")
    return value


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def audit(
    original_manifest: Path,
    original_checkpoint: Path,
    copied_manifest: Path,
    copied_checkpoint: Path,
) -> dict[str, Any]:
    if original_manifest.resolve() == copied_manifest.resolve():
        raise AssertionError("original and copied manifests must be distinct files")
    if original_checkpoint.resolve() == copied_checkpoint.resolve():
        raise AssertionError("original and copied checkpoints must be distinct files")

    original_raw, original_rows = manifest_rows(original_manifest)
    copied_raw, copied_rows = manifest_rows(copied_manifest)
    if digest_bytes(original_raw) != ORIGINAL_MANIFEST_SHA256:
        raise AssertionError("original manifest does not match the frozen stopped prefix")
    if digest(original_checkpoint) != ORIGINAL_CHECKPOINT_SHA256:
        raise AssertionError("original checkpoint does not match the frozen stopped checkpoint")
    if copied_raw != original_raw or copied_rows != original_rows:
        raise AssertionError("copied manifest differs from the original stopped prefix")
    if copied_checkpoint.read_bytes() != original_checkpoint.read_bytes():
        raise AssertionError("copied checkpoint differs byte-for-byte from the original")

    original_artifacts = validate_rows(original_manifest, original_rows)
    copied_artifacts = validate_rows(copied_manifest, copied_rows)
    if copied_artifacts != original_artifacts:
        raise AssertionError("copied artifact hash ledger differs from the original")
    validate_checkpoint(original_checkpoint, original_rows)
    validate_checkpoint(copied_checkpoint, copied_rows)

    return {
        "schema_version": 1,
        "status": "known_class_embedding_resume_prefix_audit_pass",
        "prefix_hosts": PREFIX_HOSTS,
        "next_host": PREFIX_HOSTS,
        "total_hosts": TOTAL_HOSTS,
        "original_host_gate_seconds": HOST_GATE_SECONDS,
        "original_manifest_sha256": ORIGINAL_MANIFEST_SHA256,
        "copied_manifest_sha256": digest(copied_manifest),
        "original_checkpoint_sha256": ORIGINAL_CHECKPOINT_SHA256,
        "copied_checkpoint_sha256": digest(copied_checkpoint),
        "artifact_hash_ledger_sha256": copied_artifacts,
        "continuation_scope": "fresh experiment may append canonical hosts 254..655; prefix rows and artifacts are immutable",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_manifest", type=Path)
    parser.add_argument("original_checkpoint", type=Path)
    parser.add_argument("copied_manifest", type=Path)
    parser.add_argument("copied_checkpoint", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = audit(
        args.original_manifest,
        args.original_checkpoint,
        args.copied_manifest,
        args.copied_checkpoint,
    )
    atomic_json(args.output, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
