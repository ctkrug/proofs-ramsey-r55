#!/usr/bin/env python3
"""Checkpointed two-implementation census over 328 R(5,5) graphs and complements."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import signal
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import enumerate_core_embeddings_bitset as bitset  # noqa: E402
import enumerate_core_embeddings_networkx as nximpl  # noqa: E402
import networkx as nx  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--progress", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--hosts-per-segment", type=int, default=1)
    parser.add_argument("--case-seconds", type=int, default=900)
    parser.add_argument("--host-seconds", type=float, default=30.0,
                        help="aggregate wall-clock cap across both enumerators for one host")
    parser.add_argument("--total-hosts", type=int, default=656, help="656 for the complete supplied corpus; lower only for lifecycle canaries")
    args = parser.parse_args()
    if not 1 <= args.total_hosts <= 656 or args.hosts_per_segment < 1 or args.host_seconds <= 0:
        raise SystemExit("invalid host bounds")

    def host_timeout(_signum: int, _frame: object) -> None:
        raise TimeoutError(f"aggregate host gate exceeded {args.host_seconds:g} seconds")

    signal.signal(signal.SIGALRM, host_timeout)

    corpus = Path(args.corpus)
    checkpoint_path = Path(args.checkpoint)
    progress_path = Path(args.progress)
    output = Path(args.output)
    raw = corpus.read_bytes()
    if hashlib.sha256(raw).hexdigest() != bitset.CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")
    records = raw.splitlines()
    if len(records) != 328:
        raise AssertionError("corpus coverage mismatch")
    bit_graphs = [bitset.decode_short_graph6(row) for row in records]
    nx_graphs = [nx.from_graph6_bytes(row) for row in records]
    bit_pattern = bitset.induced_pattern(bit_graphs[20])
    nx_pattern = nximpl.core_from_source(nx_graphs[20])

    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {
        "schema_version": 1, "next_host": 0, "total_hosts": args.total_hosts,
        "corpus_sha256": bitset.CORPUS_SHA256, "completed": [],
    }
    if checkpoint["corpus_sha256"] != bitset.CORPUS_SHA256 or checkpoint["total_hosts"] != args.total_hosts:
        raise AssertionError("checkpoint identity mismatch")
    manifest = output / "manifest.jsonl"
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    segment_start = checkpoint["next_host"]
    stop = min(args.total_hosts, segment_start + args.hosts_per_segment)
    for index in range(segment_start, stop):
        host_started = time.monotonic()
        source_index = index % 328
        complemented = index >= 328
        name = ("complement" if complemented else "source") + f"_record_{source_index + 1}"
        bit_host = bitset.complement(bit_graphs[source_index]) if complemented else bit_graphs[source_index]
        nx_host = nx.complement(nx_graphs[source_index]) if complemented else nx_graphs[source_index]
        left_limit = min(float(args.case_seconds), args.host_seconds)
        left = bitset.run_case(name, bit_pattern, bit_host, left_limit)
        remaining = args.host_seconds - (time.monotonic() - host_started)
        if remaining <= 0:
            raise TimeoutError(f"aggregate host gate exceeded for {name} after the bitset implementation")
        right = nximpl.process_case(name, nx_pattern, nx_host, min(float(args.case_seconds), remaining))
        host_elapsed = time.monotonic() - host_started
        if host_elapsed > args.host_seconds:
            raise TimeoutError(f"aggregate host gate exceeded for {name}")
        keys = ("embedding_count", "mapping_stream_sha256", "vector_occurrences", "unique_vector_count", "vector_stream_sha256")
        if any(left[key] != right[key] for key in keys) or left["unique_vectors"] != right["unique_vectors"]:
            raise AssertionError(f"implementation mismatch for {name}")
        artifact = output / "hosts" / f"{index:03d}-{name}.json.gz"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        temporary = artifact.with_suffix(".tmp")
        with gzip.open(temporary, "wt", encoding="utf-8") as handle:
            json.dump({"bitset": left, "networkx_summary": {key: right[key] for key in keys}}, handle, sort_keys=True)
        os.replace(temporary, artifact)
        row = {
            "host_index": index, "case": name, **{key: left[key] for key in keys},
            "artifact": artifact.relative_to(output).as_posix(), "artifact_sha256": sha256(artifact),
            "bitset_seconds": left["seconds"], "networkx_seconds": right["seconds"],
            "host_seconds": host_elapsed, "host_gate_seconds": args.host_seconds,
        }
        with manifest.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush(); os.fsync(handle.fileno())
        checkpoint["completed"].append(row)
        checkpoint["next_host"] = index + 1
        atomic_json(checkpoint_path, checkpoint)

    elapsed = time.monotonic() - started
    completed = checkpoint["next_host"]
    artifact_bytes = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
    segment_hosts = max(1, stop - segment_start)
    progress = {
        "schema_version": 1, "completed_units": completed, "total_units": args.total_hosts,
        "complete": completed >= args.total_hosts, "correctness_checks_passed": True,
        "decision_value_active": True, "artifact_bytes": artifact_bytes,
        "manifest": manifest.as_posix(), "manifest_sha256": sha256(manifest),
        "last_segment_seconds": elapsed,
        "observed_seconds_per_host": elapsed / segment_hosts,
        "projected_remaining_seconds": (args.total_hosts - completed) * elapsed / segment_hosts,
        "message": f"reconciled {completed}/{args.total_hosts} hosts with exact stream agreement",
    }
    atomic_json(progress_path, progress)
    print(json.dumps(progress, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
