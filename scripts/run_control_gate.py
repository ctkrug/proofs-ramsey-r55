#!/usr/bin/env python3
"""Compile and adversarially compare the two R55 control checkers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout)


def normalized(payload: dict[str, object]) -> list[dict[str, object]]:
    graphs = payload.get("graphs")
    if not isinstance(graphs, list):
        raise AssertionError("checker output has no graph list")
    return graphs


def expect_rejection(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode == 0:
        raise AssertionError(f"malformed input was accepted: {command}")
    return result.stderr.strip().splitlines()[-1]


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit("usage: run_control_gate.py CHECKER_A CHECKER_B_C INPUT OUTPUT")
    checker_a = Path(sys.argv[1]).resolve()
    checker_b_source = Path(sys.argv[2]).resolve()
    source = Path(sys.argv[3]).resolve()
    output = Path(sys.argv[4]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    compiler = shutil.which("gcc")
    if compiler is None:
        raise RuntimeError("gcc not found")
    with tempfile.TemporaryDirectory(prefix="r55-control-") as temporary:
        temp = Path(temporary)
        checker_b = temp / "checker_b"
        subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)],
            check=True,
        )
        base_a = [sys.executable, str(checker_a), "--format", "matrix", "--input", str(source)]
        base_b = [str(checker_b), "--format", "matrix", "--input", str(source)]

        result_a = run_json(base_a)
        result_b = run_json(base_b)
        graphs_a = normalized(result_a)
        graphs_b = normalized(result_b)
        if graphs_a != graphs_b:
            raise AssertionError("base exact outputs disagree")
        if [graph["id"] for graph in graphs_a] != ["graph1", "graph2"]:
            raise AssertionError("unexpected graph IDs")

        expected = {
            "graph1": {"zero_k5": [[0, 2, 28, 29, 38], [0, 11, 28, 29, 38]], "one_k5": []},
            "graph2": {"zero_k5": [], "one_k5": [[0, 15, 22, 28, 39], [0, 15, 24, 28, 39]]},
        }
        for graph in graphs_a:
            target = expected[graph["id"]]
            if graph["zero_k5"] != target["zero_k5"] or graph["one_k5"] != target["one_k5"]:
                raise AssertionError(f"visible-source violation identity mismatch for {graph['id']}")

        mutation_results: dict[str, object] = {}
        target_set = [0, 1, 2, 3, 4]
        for mutation, field in (("clique", "one_k5"), ("independent", "zero_k5")):
            args = ["--id", "graph2", "--force", mutation]
            mutated_a = normalized(run_json(base_a + args))
            mutated_b = normalized(run_json(base_b + args))
            if mutated_a != mutated_b:
                raise AssertionError(f"checkers disagree on {mutation} mutation")
            if target_set not in mutated_a[0][field]:
                raise AssertionError(f"{mutation} mutation did not expose target set")
            mutation_results[mutation] = {
                "target": target_set,
                "zero_count": len(mutated_a[0]["zero_k5"]),
                "one_count": len(mutated_a[0]["one_k5"]),
                "agreed": True,
            }

        graph2 = next(graph for graph in graphs_a if graph["id"] == "graph2")
        violations = graph2["zero_k5"] + graph2["one_k5"]
        intersection = sorted(set(violations[0]).intersection(violations[1]))
        union = sorted(set(violations[0]).union(violations[1]))
        if len(intersection) != 4 or len(union) != 6:
            raise AssertionError("two-conflict support does not have intersection 4 / union 6")
        deletion_results = []
        for vertex in intersection:
            args = ["--id", "graph2", "--delete", str(vertex)]
            deleted_a = normalized(run_json(base_a + args))
            deleted_b = normalized(run_json(base_b + args))
            if deleted_a != deleted_b:
                raise AssertionError(f"checkers disagree after deleting vertex {vertex}")
            if deleted_a[0]["zero_k5"] or deleted_a[0]["one_k5"]:
                raise AssertionError(f"deletion {vertex} retained a forbidden 5-set")
            deletion_results.append({"vertex": vertex, "n": deleted_a[0]["n"], "valid": True})

        rows = [line for line in source.read_text(encoding="ascii").splitlines() if line and not line.startswith("#")]
        first_matrix_row = next(index for index, line in enumerate(rows) if not line.startswith("> "))
        malformed = {}
        truncated = temp / "truncated.txt"
        truncated.write_text("\n".join(rows[:-1]) + "\n", encoding="ascii")
        malformed["truncated"] = {
            "checker_a": expect_rejection([sys.executable, str(checker_a), "--format", "matrix", "--input", str(truncated)]),
            "checker_b": expect_rejection([str(checker_b), "--format", "matrix", "--input", str(truncated)]),
        }
        invalid = temp / "invalid.txt"
        invalid_rows = rows[:]
        invalid_rows[first_matrix_row] = "x" + invalid_rows[first_matrix_row][1:]
        invalid.write_text("\n".join(invalid_rows) + "\n", encoding="ascii")
        malformed["invalid_character"] = {
            "checker_a": expect_rejection([sys.executable, str(checker_a), "--format", "matrix", "--input", str(invalid)]),
            "checker_b": expect_rejection([str(checker_b), "--format", "matrix", "--input", str(invalid)]),
        }
        asymmetric = temp / "asymmetric.txt"
        asymmetric_rows = rows[:]
        row = list(asymmetric_rows[first_matrix_row])
        row[1] = "1" if row[1] == "0" else "0"
        asymmetric_rows[first_matrix_row] = "".join(row)
        asymmetric.write_text("\n".join(asymmetric_rows) + "\n", encoding="ascii")
        malformed["asymmetric"] = {
            "checker_a": expect_rejection([sys.executable, str(checker_a), "--format", "matrix", "--input", str(asymmetric)]),
            "checker_b": expect_rejection([str(checker_b), "--format", "matrix", "--input", str(asymmetric)]),
        }

        report = {
            "schema_version": 1,
            "status": "provisional_control_pass_source_gate_open",
            "scope": "two visible third-party K43 matrices only; not the 328-record source corpus",
            "source": {
                "path": str(source),
                "sha256": digest(source),
                "provenance": "manually transcribed from visible indexed GitHub Gist HTML",
                "publisher_authentication": False,
            },
            "checker_a": {"path": str(checker_a), "sha256": digest(checker_a), "method": result_a["checker"]},
            "checker_b": {"path": str(checker_b_source), "sha256": digest(checker_b_source), "method": result_b["checker"]},
            "base_graphs": graphs_a,
            "semantic_mutations": mutation_results,
            "parser_rejections": malformed,
            "graph2_conflict_support": {"intersection": intersection, "union": union},
            "graph2_valid_deletions": deletion_results,
            "unclosed_gates": [
                "raw McKay r55_42some.g6 bytes not acquired",
                "raw Springer Supplementary Data 4 bytes not acquired",
                "no canonical-isomorphism comparison to the 656 controls",
            ],
        }
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "report": str(output),
            "report_sha256": digest(output),
            "base_violation_counts": {
                graph["id"]: {"zero": len(graph["zero_k5"]), "one": len(graph["one_k5"])} for graph in graphs_a
            },
            "graph2_conflict_support": report["graph2_conflict_support"],
            "valid_deletions": deletion_results,
            "unclosed_gates": report["unclosed_gates"],
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

