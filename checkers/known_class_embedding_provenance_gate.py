#!/usr/bin/env python3
"""Audit frozen producer provenance and operational gates for a census prefix.

This checker does not validate embeddings.  It complements the cold mathematical
audit by verifying that every recorded lab segment names a Git revision containing
the same driver and imported enumerator bytes, that current inputs still match
those bytes, and that the immutable host ledger satisfies the predeclared resource
gates.  Its scope is exactly the prefix recorded in the supplied job state.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


DRIVER = "scripts/run_known_class_embedding_census.py"
BITSET = "scripts/enumerate_core_embeddings_bitset.py"
VF2 = "scripts/enumerate_core_embeddings_networkx.py"
CORPUS = "sources/r55_42some.g6"
PRODUCERS = (DRIVER, BITSET, VF2)
MIN_THROUGHPUT = 0.001
MAX_ARTIFACT_GROWTH = 200_000_000
MAX_HOST_SECONDS = 30.0
MAX_MEMORY_KIB = 1024 * 1024
MAX_TIED_ROW_VECTORS = 100_000


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def git_bytes(repo: Path, revision: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    ).stdout


def require_clean_tracked_file(repo: Path, path: str) -> None:
    for cached in (False, True):
        command = ["git", "diff", "--quiet"]
        if cached:
            command.append("--cached")
        command.extend(["--", path])
        result = subprocess.run(command, cwd=repo, timeout=30)
        if result.returncode != 0:
            raise AssertionError(f"tracked producer differs from Git index/HEAD: {path}")


def main() -> int:
    if len(sys.argv) != 7:
        raise SystemExit(
            "usage: known_class_embedding_provenance_gate.py "
            "REPO JOB.json MANIFEST.jsonl CHECKPOINT.json PROGRESS.json OUTPUT.json"
        )
    repo, job_path, manifest_path, checkpoint_path, progress_path, output_path = map(
        Path, sys.argv[1:]
    )
    repo = repo.resolve()
    job = json.loads(job_path.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    progress = json.loads(progress_path.read_text(encoding="utf-8"))

    if job["id"] != "lab-ramsey-r55-872a7c3ee855":
        raise AssertionError("unexpected job identity")
    segments = job["segments"]
    expected_count = int(job["latest_progress"]["completed_units"])
    if expected_count != len(rows) or checkpoint["next_host"] != expected_count:
        raise AssertionError("job, checkpoint, and manifest prefix lengths differ")
    if [row["host_index"] for row in rows] != list(range(expected_count)):
        raise AssertionError("manifest is not a contiguous canonical prefix")
    if [segment["segment"] for segment in segments] != list(range(1, expected_count + 1)):
        raise AssertionError("lab segment records are not contiguous")
    if progress["manifest_sha256"] != digest_file(manifest_path):
        raise AssertionError("progress does not hash the current manifest")
    latest = job["latest_progress"]
    if latest["sha256"] != digest_file(progress_path):
        raise AssertionError("job does not hash the current progress record")
    if segments[-1]["checkpoint_sha256"] != digest_file(checkpoint_path):
        raise AssertionError("latest lab segment does not hash the current checkpoint")

    current_hashes = {path: digest_file(repo / path) for path in PRODUCERS}
    current_hashes[CORPUS] = digest_file(repo / CORPUS)
    for path in PRODUCERS:
        require_clean_tracked_file(repo, path)
    if job["input_sha256"][DRIVER] != current_hashes[DRIVER]:
        raise AssertionError("current driver differs from submitted driver")
    if job["input_sha256"][CORPUS] != current_hashes[CORPUS]:
        raise AssertionError("current corpus differs from submitted corpus")

    revision_hashes: dict[str, set[str]] = {path: set() for path in PRODUCERS}
    revisions: list[str] = []
    max_memory_kib = 0
    min_segment_throughput = float("inf")
    max_segment_growth = 0
    for expected_segment, segment in enumerate(segments, start=1):
        if segment["segment"] != expected_segment or segment["returncode"] != 0:
            raise AssertionError(f"failed or displaced segment {expected_segment}")
        if segment["threshold_failures"]:
            raise AssertionError(f"recorded threshold failure in segment {expected_segment}")
        recorded_progress = segment["progress"]
        min_segment_throughput = min(
            min_segment_throughput, float(recorded_progress["throughput_per_second"])
        )
        max_segment_growth = max(
            max_segment_growth, int(recorded_progress["artifact_growth_bytes"])
        )
        runner = json.loads(segment["runner_result"])
        if runner["returncode"] != 0 or runner["timed_out"]:
            raise AssertionError(f"runner failure in segment {expected_segment}")
        if runner["command"] != job["command"]:
            raise AssertionError(f"command drift in segment {expected_segment}")
        inputs = runner["input_artifacts"]
        for relative, expected_hash in job["input_sha256"].items():
            absolute = str((repo / relative).resolve())
            if inputs.get(absolute) != expected_hash:
                raise AssertionError(
                    f"recorded input drift for {relative} in segment {expected_segment}"
                )
        revision = runner["git_commit"]
        if not revision:
            raise AssertionError(f"missing Git revision in segment {expected_segment}")
        revisions.append(revision)
        for path in PRODUCERS:
            revision_hashes[path].add(digest_bytes(git_bytes(repo, revision, path)))
        max_memory_kib = max(max_memory_kib, int(runner["peak_child_memory_rusage"]))

    for path in PRODUCERS:
        if revision_hashes[path] != {current_hashes[path]}:
            raise AssertionError(f"producer bytes changed across recorded revisions: {path}")

    host_seconds = [
        float(row["bitset_seconds"]) + float(row["networkx_seconds"]) for row in rows
    ]
    tied_vectors = [int(row["vector_occurrences"]) for row in rows]
    if max(host_seconds) >= MAX_HOST_SECONDS:
        raise AssertionError("aggregate per-host 30-second gate failed")
    if max(tied_vectors) >= MAX_TIED_ROW_VECTORS:
        raise AssertionError("tied-row vector gate failed")
    if min_segment_throughput < MIN_THROUGHPUT:
        raise AssertionError("segment throughput gate failed")
    if max_segment_growth >= MAX_ARTIFACT_GROWTH:
        raise AssertionError("artifact growth gate failed")
    if max_memory_kib >= MAX_MEMORY_KIB:
        raise AssertionError("memory gate failed")

    report = {
        "schema_version": 1,
        "status": "known_class_embedding_recorded_revision_gate_pass",
        "scope": f"exactly lab segments and canonical hosts 0..{expected_count - 1}",
        "job_id": job["id"],
        "segments": len(segments),
        "producer_hashes": current_hashes,
        "distinct_recorded_git_revisions": len(set(revisions)),
        "operational_gates": {
            "max_aggregate_host_seconds": max(host_seconds),
            "max_aggregate_host_seconds_host": max(
                range(len(host_seconds)), key=host_seconds.__getitem__
            ),
            "max_tied_row_vector_occurrences": max(tied_vectors),
            "min_segment_throughput_per_second": min_segment_throughput,
            "max_segment_artifact_growth_bytes": max_segment_growth,
            "max_peak_child_memory_kib": max_memory_kib,
        },
        "hashes": {
            "job_state": digest_file(job_path),
            "manifest": digest_file(manifest_path),
            "checkpoint": digest_file(checkpoint_path),
            "progress": digest_file(progress_path),
        },
        "qualification": (
            "The submitted lab spec hashes the driver and corpus but not imported modules, "
            "and its runner does not record historical worktree dirtiness. This gate proves "
            "only that every recorded Git revision contains identical producer bytes and "
            "that the current tracked producer files are clean. It cannot exclude a temporary "
            "uncommitted imported-module edit during a past segment, cannot make the original "
            "spec self-hashing, and does not certify future segments."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
