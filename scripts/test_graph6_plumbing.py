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

from run_corpus_gate import complement_graph6


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


def networkx_signature(record: bytes) -> tuple[int, int, list[int]]:
    graph = nx.from_graph6_bytes(record)
    return graph.number_of_nodes(), graph.number_of_edges(), [degree for _, degree in graph.degree()]


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
        source = temp / "all-order7.g6"
        ours = temp / "ours-complement.g6"
        nauty = temp / "nauty-complement.g6"
        checker_b = temp / "checker_b"
        subprocess.run([required["nauty-geng"], "-q", "7", str(source)], check=True)
        records = source.read_bytes().splitlines()
        if len(records) != 1_044:
            raise AssertionError(f"nauty-geng produced {len(records)} records, expected 1044")
        complements = [complement_graph6(record) for record in records]
        if [complement_graph6(record) for record in complements] != records:
            raise AssertionError("local complement transformation is not an involution")
        ours.write_bytes(b"\n".join(complements) + b"\n")
        subprocess.run([required["nauty-complg"], "-q", str(source), str(nauty)], check=True)
        if ours.read_bytes() != nauty.read_bytes():
            raise AssertionError("local complement bytes disagree with nauty-complg")

        subprocess.run(
            [required["gcc"], "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)],
            check=True,
        )
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
                n, edges, degrees = networkx_signature(record)
                if (checked["n"], checked["edges"], checked["degrees"]) != (n, edges, degrees):
                    raise AssertionError(f"NetworkX signature disagreement on {label} record {index}")
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
            "checker_exact_output_agreement": True,
            "networkx_signature_agreement": True,
            "methods": {
                "checker_a": "direct combinations over independently parsed Boolean matrices",
                "checker_b": "recursive bitset clique enumeration over separately parsed records",
                "complement_reference": required["nauty-complg"],
                "suite_generator": required["nauty-geng"],
                "third_parser": f"networkx {nx.__version__}",
            },
            "checker_hashes": {"checker_a": digest(checker_a), "checker_b_source": digest(checker_b_source)},
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
