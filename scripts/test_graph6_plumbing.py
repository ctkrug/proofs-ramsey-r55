#!/usr/bin/env python3
"""Cross-check graph6 parsing and complementation on every order-7 isomorphism class."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import networkx as nx

import run_corpus_gate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout)


def graph_list(payload: dict[str, object]) -> list[dict[str, object]]:
    graphs = payload.get("graphs")
    if not isinstance(graphs, list):
        raise AssertionError("checker output has no graph list")
    return graphs


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: test_graph6_plumbing.py CHECKER_A CHECKER_B_C OUTPUT")
    checker_a = Path(sys.argv[1]).resolve()
    checker_b_source = Path(sys.argv[2]).resolve()
    output = Path(sys.argv[3]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    required = {name: shutil.which(name) for name in ("gcc", "nauty-geng", "nauty-complg")}
    missing = [name for name, path in required.items() if path is None]
    if missing:
        raise RuntimeError(f"required tools missing: {', '.join(missing)}")

    with tempfile.TemporaryDirectory(prefix="r55-g6-test-") as temporary:
        temp = Path(temporary)
        fixture_body = temp / "fixture.g6"
        fixture_headers = temp / "fixture.headers"
        fixture_transfer = temp / "fixture-transfer.json"
        fixture_experiment = temp / "fixture-experiment.json"
        fixture_body.write_bytes(b"fixture")
        fixture_headers.write_bytes(b"HTTP/2 200\r\nserver: fixture\r\ncontent-length: 7\r\n\r\n")
        fixture_transfer.write_text(json.dumps({
            "http_code": 200,
            "response_code": 200,
            "url_effective": run_corpus_gate.AUTHORITATIVE_SOURCE,
            "size_download": 7,
            "ssl_verify_result": 0,
            "content_type": None,
        }) + "\n", encoding="utf-8")
        fixture_experiment.write_text(json.dumps({
            "returncode": 0,
            "source_urls": [run_corpus_gate.AUTHORITATIVE_SOURCE],
        }) + "\n", encoding="utf-8")
        provenance_control = {
            "schema_version": 2,
            "source_authority": "authoritative_direct",
            "requested_url": run_corpus_gate.AUTHORITATIVE_SOURCE,
            "final_url": run_corpus_gate.AUTHORITATIVE_SOURCE,
            "retrieved_at_utc": "2000-01-01T00:00:00Z",
            "acquisition_method": "regression-fixture",
            "response_status": 200,
            "content_type": None,
            "content_type_inferred": False,
            "response_headers": {"server": "fixture", "content-length": "7"},
            "sha256": digest(fixture_body),
            "byte_count": 7,
            "header_capture": {
                "path": fixture_headers.name,
                "sha256": digest(fixture_headers),
                "byte_count": fixture_headers.stat().st_size,
            },
            "retrieved_body": {
                "path": fixture_body.name,
                "sha256": digest(fixture_body),
                "byte_count": fixture_body.stat().st_size,
            },
            "transfer_metadata_capture": {
                "path": fixture_transfer.name,
                "sha256": digest(fixture_transfer),
            },
            "retrieval_experiment": {
                "path": fixture_experiment.name,
                "sha256": digest(fixture_experiment),
            },
        }
        run_corpus_gate.validate_provenance(provenance_control, digest(fixture_body), 7, temp)
        rejected_provenance_mutations = []
        mutations = (
            ("source_authority", lambda value: value.__setitem__("source_authority", "mirror")),
            ("byte_count", lambda value: value.__setitem__("byte_count", 8)),
            ("content_type_inferred", lambda value: value.__setitem__("content_type_inferred", True)),
            ("header_capture_sha256", lambda value: value["header_capture"].__setitem__("sha256", "0" * 64)),
        )
        for field, mutate in mutations:
            mutation = json.loads(json.dumps(provenance_control))
            mutate(mutation)
            try:
                run_corpus_gate.validate_provenance(mutation, digest(fixture_body), 7, temp)
            except ValueError:
                rejected_provenance_mutations.append(field)
            else:
                raise AssertionError(f"provenance mutation {field} was not rejected")

        source = temp / "all-order7.g6"
        ours = temp / "ours-complement.g6"
        nauty = temp / "nauty-complement.g6"
        checker_b = temp / "checker_b"
        subprocess.run([required["nauty-geng"], "-q", "7", str(source)], check=True)
        records = source.read_bytes().splitlines()
        if len(records) != 1_044:
            raise AssertionError(f"nauty-geng produced {len(records)} records, expected 1044")
        complements = [run_corpus_gate.complement_graph6(record) for record in records]
        if [run_corpus_gate.complement_graph6(record) for record in complements] != records:
            raise AssertionError("local complement transformation is not an involution")
        ours.write_bytes(b"\n".join(complements) + b"\n")
        reference_records = run_corpus_gate.nauty_file_transform(required["nauty-complg"], source, nauty)
        if ours.read_bytes() != nauty.read_bytes():
            raise AssertionError("local complement bytes disagree with nauty-complg")
        if reference_records != complements:
            raise AssertionError("local complement records disagree with nauty-complg")
        tampered = bytearray(ours.read_bytes())
        tampered[1] = ((tampered[1] - 63) ^ 32) + 63
        if bytes(tampered) == nauty.read_bytes():
            raise AssertionError("one-bit complement mutation was not distinguished from nauty output")

        subprocess.run(
            [required["gcc"], "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)],
            check=True,
        )
        checker_b_binary_sha256 = digest(checker_b)
        payloads = {}
        for label, path in (("source", source), ("complement", ours)):
            result_a = run_json([sys.executable, str(checker_a), "--format", "graph6", "--input", str(path)])
            result_b = run_json([str(checker_b), "--format", "graph6", "--input", str(path)])
            graphs_a = graph_list(result_a)
            graphs_b = graph_list(result_b)
            if graphs_a != graphs_b:
                raise AssertionError(f"checker disagreement on {label} suite")
            selected_records = records if label == "source" else complements
            for index, (record, checked) in enumerate(zip(selected_records, graphs_a, strict=True), 1):
                n, edges, degrees, upper_triangle_bits = run_corpus_gate.networkx_signature(record)
                if (
                    checked["n"],
                    checked["edges"],
                    checked["degrees"],
                    checked["upper_triangle_bits"],
                ) != (n, edges, degrees, upper_triangle_bits):
                    raise AssertionError(f"NetworkX full-adjacency disagreement on {label} record {index}")
            payloads[label] = graphs_a

        report = {
            "schema_version": 1,
            "status": "graph6_plumbing_pass",
            "scope": "one representative of every one of the 1044 unlabeled simple graphs on 7 vertices",
            "why_order_7": "C(7,2)=21 leaves three graph6 padding bits, the same padding count as C(42,2)=861",
            "generated_records": len(records),
            "source_suite_sha256": digest(source),
            "complement_suite_sha256": digest(ours),
            "complement_involution": True,
            "complement_exact_byte_agreement_with_nauty": True,
            "one_bit_complement_mutation_detected": True,
            "provenance_schema_control": {
                "valid_fixture_accepted": True,
                "rejected_mutations": rejected_provenance_mutations,
            },
            "checker_exact_output_agreement": True,
            "networkx_full_adjacency_agreement": True,
            "methods": {
                "checker_a": "direct combinations over independently parsed Boolean matrices",
                "checker_b": "recursive bitset clique enumeration over separately parsed records",
                "complement_reference": required["nauty-complg"],
                "suite_generator": required["nauty-geng"],
                "third_parser": f"networkx {nx.__version__}; full upper-triangle bitstring",
            },
            "checker_hashes": {
                "checker_a": digest(checker_a),
                "checker_b_source": digest(checker_b_source),
                "checker_b_binary": checker_b_binary_sha256,
            },
            "imported_corpus_gate_hash": digest(Path(run_corpus_gate.__file__).resolve()),
            "aggregate_forbidden_sets": {
                label: {
                    "zero_k5": sum(len(graph["zero_k5"]) for graph in graphs),
                    "one_k5": sum(len(graph["one_k5"]) for graph in graphs),
                }
                for label, graphs in payloads.items()
            },
        }
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "scope": report["scope"],
            "report": str(output),
            "report_sha256": digest(output),
            "aggregate_forbidden_sets": report["aggregate_forbidden_sets"],
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
