#!/usr/bin/env python3
"""Fail-closed authentication and dual-check gate for McKay's R(5,5,42) corpus."""

from __future__ import annotations

from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


EXPECTED_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
EXPECTED_BYTES = 47_888
EXPECTED_RECORDS = 328
EXPECTED_EDGE_HISTOGRAM = {423: 1, 424: 7, 425: 29, 426: 66, 427: 89, 428: 77, 429: 43, 430: 16}


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout)


def graph_list(payload: dict[str, object]) -> list[dict[str, object]]:
    value = payload.get("graphs")
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise AssertionError("checker output has no graph-object list")
    return value


def graph6_records(raw: bytes) -> list[bytes]:
    records = raw.splitlines()
    if raw and not raw.endswith(b"\n"):
        raise ValueError("corpus does not end with LF")
    if any(not record for record in records):
        raise ValueError("corpus contains a blank graph6 record")
    return records


def networkx_signature(record: bytes) -> tuple[int, int, list[int]]:
    """Decode through an external parser and return only representation-neutral data."""
    try:
        import networkx as nx
    except ImportError as error:
        raise RuntimeError("networkx is required for the third graph6 parser gate") from error
    graph = nx.from_graph6_bytes(record)
    return graph.number_of_nodes(), graph.number_of_edges(), [degree for _, degree in graph.degree()]


def complement_graph6(record: bytes) -> bytes:
    if not record or not 63 <= record[0] <= 125:
        raise ValueError("only short graph6 records are supported")
    n = record[0] - 63
    edge_bits = n * (n - 1) // 2
    encoded = (edge_bits + 5) // 6
    if len(record) != encoded + 1:
        raise ValueError("wrong graph6 record length")
    output = bytearray([record[0]])
    cursor = 0
    for byte in record[1:]:
        value = byte - 63
        if not 0 <= value < 64:
            raise ValueError("invalid graph6 byte")
        next_value = 0
        for shift in range(5, -1, -1):
            if cursor < edge_bits:
                next_value |= (1 - ((value >> shift) & 1)) << shift
            elif (value >> shift) & 1:
                raise ValueError("nonzero graph6 padding bit")
            cursor += 1
        output.append(next_value + 63)
    return bytes(output)


def nauty_version(program: str) -> str:
    result = subprocess.run([program, "-help"], text=True, capture_output=True)
    combined = (result.stdout + result.stderr).strip().splitlines()
    return combined[0] if combined else "version unavailable"


def canonical_lines(labelg: str, source: Path, destination: Path) -> list[bytes]:
    result = subprocess.run([labelg, "-q", str(source), str(destination)], text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"nauty-labelg failed: {result.stderr.strip()}")
    if result.stdout.strip() or result.stderr.strip():
        raise RuntimeError("nauty-labelg -q produced unexpected diagnostics")
    return destination.read_bytes().splitlines()


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit("usage: run_corpus_gate.py CHECKER_A CHECKER_B_C CORPUS OUTPUT")
    checker_a = Path(sys.argv[1]).resolve()
    checker_b_source = Path(sys.argv[2]).resolve()
    corpus = Path(sys.argv[3]).resolve()
    output = Path(sys.argv[4]).resolve()

    expected = {
        "sha256": EXPECTED_SHA256,
        "bytes": EXPECTED_BYTES,
        "records": EXPECTED_RECORDS,
        "metadata_source": "https://huggingface.co/datasets/linxy/RamseyGraph/blob/main/data/r55_42some.g6",
        "authoritative_source": "https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6",
        "qualification": "mirror hash/size are an acquisition discriminator, not authentication of the authoritative bytes",
    }
    if not corpus.is_file():
        report = {
            "schema_version": 1,
            "status": "source_preflight_failed",
            "failure": "corpus file is absent",
            "expected": expected,
            "actual": {"path": str(corpus), "exists": False},
            "downstream_checks_run": False,
        }
        write_report(output, report)
        print(json.dumps({"status": report["status"], "failure": report["failure"], "report": str(output)}, sort_keys=True))
        return 2

    raw = corpus.read_bytes()
    try:
        records = graph6_records(raw)
    except ValueError as error:
        records = raw.splitlines()
        record_error = str(error)
    else:
        record_error = ""
    actual = {
        "path": str(corpus),
        "exists": True,
        "sha256": digest_bytes(raw),
        "bytes": len(raw),
        "records": len(records),
        "record_format_error": record_error,
    }
    mismatches = []
    for field in ("sha256", "bytes", "records"):
        if actual[field] != expected[field]:
            mismatches.append({"field": field, "expected": expected[field], "actual": actual[field]})
    if record_error:
        mismatches.append({"field": "record_format", "expected": "one nonblank LF-terminated graph6 record per line", "actual": record_error})
    if mismatches:
        report = {
            "schema_version": 1,
            "status": "source_preflight_failed",
            "failure": "source bytes do not match the frozen acquisition discriminator",
            "expected": expected,
            "actual": actual,
            "mismatches": mismatches,
            "downstream_checks_run": False,
        }
        write_report(output, report)
        print(json.dumps({"status": report["status"], "mismatches": mismatches, "report": str(output)}, sort_keys=True))
        return 2

    compiler = shutil.which("gcc")
    labelg = shutil.which("nauty-labelg")
    if compiler is None or labelg is None:
        missing = [name for name, value in (("gcc", compiler), ("nauty-labelg", labelg)) if value is None]
        raise RuntimeError(f"required tools missing: {', '.join(missing)}")

    complements = [complement_graph6(record) for record in records]
    if [complement_graph6(record) for record in complements] != records:
        raise AssertionError("graph6 complement is not an involution")

    with tempfile.TemporaryDirectory(prefix="r55-corpus-") as temporary:
        temp = Path(temporary)
        complement_path = temp / "complements.g6"
        complement_path.write_bytes(b"\n".join(complements) + b"\n")
        checker_b = temp / "checker_b"
        subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)],
            check=True,
        )
        base_a_payload = run_json([sys.executable, str(checker_a), "--format", "graph6", "--input", str(corpus)])
        base_b_payload = run_json([str(checker_b), "--format", "graph6", "--input", str(corpus)])
        comp_a_payload = run_json([sys.executable, str(checker_a), "--format", "graph6", "--input", str(complement_path)])
        comp_b_payload = run_json([str(checker_b), "--format", "graph6", "--input", str(complement_path)])
        base_a, base_b = graph_list(base_a_payload), graph_list(base_b_payload)
        comp_a, comp_b = graph_list(comp_a_payload), graph_list(comp_b_payload)
        if base_a != base_b:
            raise AssertionError("base-corpus checker outputs disagree")
        if comp_a != comp_b:
            raise AssertionError("complement-corpus checker outputs disagree")
        if len(base_a) != EXPECTED_RECORDS or len(comp_a) != EXPECTED_RECORDS:
            raise AssertionError("checker record count mismatch")

        base_networkx = [networkx_signature(record) for record in records]
        comp_networkx = [networkx_signature(record) for record in complements]

        for index, (base, complement, base_nx, complement_nx) in enumerate(
            zip(base_a, comp_a, base_networkx, comp_networkx, strict=True), 1
        ):
            if base["n"] != 42 or complement["n"] != 42:
                raise AssertionError(f"record {index}: graph order is not 42")
            if (base["n"], base["edges"], base["degrees"]) != base_nx:
                raise AssertionError(f"record {index}: NetworkX source signature disagreement")
            if (complement["n"], complement["edges"], complement["degrees"]) != complement_nx:
                raise AssertionError(f"record {index}: NetworkX complement signature disagreement")
            for item, kind in ((base, "base"), (complement, "complement")):
                if item["zero_k5"] or item["one_k5"]:
                    raise AssertionError(f"record {index} {kind}: forbidden 5-set found")
            if complement["edges"] != 861 - base["edges"]:
                raise AssertionError(f"record {index}: complement edge count mismatch")
            if complement["degrees"] != [41 - value for value in base["degrees"]]:
                raise AssertionError(f"record {index}: complement degree sequence mismatch")

        edge_histogram = dict(sorted(Counter(graph["edges"] for graph in base_a).items()))
        if edge_histogram != EXPECTED_EDGE_HISTOGRAM:
            raise AssertionError(f"base edge histogram mismatch: {edge_histogram}")
        all_degrees = [degree for graph in base_a + comp_a for degree in graph["degrees"]]
        if min(all_degrees) != 19 or max(all_degrees) != 22:
            raise AssertionError(f"unexpected degree range: {min(all_degrees)}..{max(all_degrees)}")

        base_canonical_path = temp / "base-canonical.g6"
        comp_canonical_path = temp / "comp-canonical.g6"
        base_canonical = canonical_lines(labelg, corpus, base_canonical_path)
        comp_canonical = canonical_lines(labelg, complement_path, comp_canonical_path)
        canonical_all = base_canonical + comp_canonical
        if len(canonical_all) != 656 or len(set(canonical_all)) != 656:
            raise AssertionError("nauty canonical labels do not give 656 distinct classes")

        manifest = []
        for index, (record, complement, base_label, comp_label) in enumerate(
            zip(records, complements, base_canonical, comp_canonical, strict=True), 1
        ):
            manifest.append({
                "record": index,
                "source_sha256": digest_bytes(record + b"\n"),
                "complement_sha256": digest_bytes(complement + b"\n"),
                "source_canonical_sha256": digest_bytes(base_label + b"\n"),
                "complement_canonical_sha256": digest_bytes(comp_label + b"\n"),
                "source_edges": base_a[index - 1]["edges"],
                "complement_edges": comp_a[index - 1]["edges"],
            })

        report = {
            "schema_version": 1,
            "status": "corpus_control_pass",
            "claim_scope": "328 supplied source records and their 328 derived complements only; not corpus completeness",
            "source": actual,
            "expected": expected,
            "checker_a": {"path": str(checker_a), "sha256": digest(checker_a), "method": base_a_payload["checker"]},
            "checker_b": {"path": str(checker_b_source), "sha256": digest(checker_b_source), "method": base_b_payload["checker"]},
            "third_parser": {
                "method": "NetworkX from_graph6_bytes; order/edge-count/ordered-degree signature only",
                "version": importlib.metadata.version("networkx"),
                "source_and_complement_signature_agreement": True,
            },
            "canonicalizer": {"path": labelg, "version_probe": nauty_version(labelg)},
            "checked_instances": 656,
            "forbidden_sets": {"zero_k5": 0, "one_k5": 0},
            "base_edge_histogram": {str(key): value for key, value in edge_histogram.items()},
            "degree_range_all_656": [min(all_degrees), max(all_degrees)],
            "complement_involution": True,
            "canonical_distinct_classes": len(set(canonical_all)),
            "per_record_manifest": manifest,
        }
        write_report(output, report)
        print(json.dumps({
            "status": report["status"],
            "report": str(output),
            "report_sha256": digest(output),
            "checked_instances": report["checked_instances"],
            "canonical_distinct_classes": report["canonical_distinct_classes"],
            "base_edge_histogram": report["base_edge_histogram"],
            "degree_range_all_656": report["degree_range_all_656"],
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
