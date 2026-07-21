#!/usr/bin/env python3
"""Fail-closed provenance and complete radius-two gate for Springer Data 4."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time

import run_publisher_radius1_gate as radius1


ORDER = 43
EDGE_COUNT = ORDER * (ORDER - 1) // 2
PAIR_COUNT = EDGE_COUNT * (EDGE_COUNT - 1) // 2
INTERSECTION = [6, 12, 36, 42]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(command: list[str]) -> tuple[dict[str, object], float]:
    started = time.monotonic()
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    elapsed = time.monotonic() - started
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout), elapsed


def expect_rejection(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode == 0:
        raise AssertionError(f"malformed input was accepted: {command}")
    lines = result.stderr.strip().splitlines()
    return lines[-1] if lines else f"exit {result.returncode}"


def ordered_edges() -> list[tuple[int, int]]:
    return [(u, v) for u in range(ORDER) for v in range(u + 1, ORDER)]


def ordered_pairs() -> list[tuple[int, int]]:
    return [(first, second) for first in range(EDGE_COUNT) for second in range(first + 1, EDGE_COUNT)]


def normalized_record(record: dict[str, object]) -> dict[str, object]:
    return {
        "edge_indices": record["edge_indices"],
        "edges": record["edges"],
        "zero_k5": sorted(record["zero_k5"]),
        "one_k5": sorted(record["one_k5"]),
        "total_burden": record["total_burden"],
    }


def eligible_deletion_remainder_change(edge_pair: tuple[int, int], edges: list[tuple[int, int]]) -> bool:
    first, second = (edges[index] for index in edge_pair)
    return all(not (vertex in first and vertex in second) for vertex in INTERSECTION)


def family_summary(
    scores: list[int],
    pairs: list[tuple[int, int]],
    edges: list[tuple[int, int]],
    predicate,
    predicate_text: str,
    records: dict[tuple[int, int], dict[str, object]],
) -> dict[str, object]:
    selected = [(pair, score) for pair, score in zip(pairs, scores, strict=True) if predicate(pair)]
    minimum = min(score for _, score in selected)
    minimizers = [records[pair] for pair, score in selected if score == minimum]
    return {
        "predicate": predicate_text,
        "pairs": len(selected),
        "minimum_total_burden": minimum,
        "score_histogram": {
            str(key): value for key, value in sorted(Counter(score for _, score in selected).items())
        },
        "minimizers": minimizers,
    }


def main() -> int:
    if len(sys.argv) != 8:
        raise SystemExit(
            "usage: run_publisher_radius2_gate.py CHECKER_A CHECKER_B_C BODY1 BODY2 "
            "RADIUS1_REPORT LEDGER OUTPUT"
        )
    checker_a = Path(sys.argv[1]).resolve()
    checker_b_source = Path(sys.argv[2]).resolve()
    body1 = Path(sys.argv[3]).resolve()
    body2 = Path(sys.argv[4]).resolve()
    radius1_report_path = Path(sys.argv[5]).resolve()
    ledger_path = Path(sys.argv[6]).resolve()
    output = Path(sys.argv[7]).resolve()
    root = Path.cwd().resolve()

    frozen_bodies = [(root / descriptor["body"]).resolve() for descriptor in radius1.RETRIEVALS]
    if [body1, body2] != frozen_bodies:
        raise ValueError("body arguments are not the two frozen retrieval paths")
    retrievals = [radius1.validate_retrieval(root, descriptor) for descriptor in radius1.RETRIEVALS]
    if body1.read_bytes() != body2.read_bytes():
        raise AssertionError("the two publisher retrieval bodies differ")
    radius1_report = json.loads(radius1_report_path.read_text(encoding="utf-8"))
    if radius1_report.get("status") != "publisher_seed_radius1_pass":
        raise ValueError("the frozen radius-one gate is not admitted")
    if radius1_report.get("source", {}).get("body_sha256") != radius1.BODY_SHA256:
        raise ValueError("radius-one report is linked to a different source body")

    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise RuntimeError("a C compiler is required")
    edges = ordered_edges()
    pairs = ordered_pairs()
    pair_to_position = {pair: position for position, pair in enumerate(pairs)}
    if len(edges) != EDGE_COUNT or len(pairs) != PAIR_COUNT:
        raise AssertionError("edge or pair cardinality mismatch")

    with tempfile.TemporaryDirectory(prefix="r55-publisher-radius2-") as temporary:
        temp = Path(temporary)
        checker_b = temp / "publisher_radius2_b"
        compile_command = [
            compiler,
            "-std=c11",
            "-O3",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(checker_b_source),
            "-o",
            str(checker_b),
        ]
        subprocess.run(compile_command, check=True)

        payload_a, elapsed_a = run_json([sys.executable, str(checker_a), str(body1)])
        payload_b, elapsed_b = run_json([str(checker_b), str(body1)])
        for payload in (payload_a, payload_b):
            if payload.get("order") != ORDER or payload.get("pair_count") != PAIR_COUNT:
                raise AssertionError("checker order or pair cardinality mismatch")
            if payload.get("edge_order") != "(u,v) lexicographic for 0 <= u < v < 43":
                raise AssertionError("checker edge-order declaration mismatch")
            if payload.get("pair_order") != "(first_edge_index,second_edge_index) lexicographic with first < second":
                raise AssertionError("checker pair-order declaration mismatch")
        if payload_a.get("seed_edges") != 454:
            raise AssertionError("publisher seed edge count mismatch")
        if payload_a.get("seed_zero_k5") != radius1.EXPECTED_ZERO or payload_a.get("seed_one_k5") != radius1.EXPECTED_ONE:
            raise AssertionError("publisher seed conflict identity mismatch")

        scores_a = payload_a["scores"]
        scores_b = payload_b["scores"]
        if not isinstance(scores_a, list) or len(scores_a) != PAIR_COUNT or scores_a != scores_b:
            raise AssertionError("independent checkers disagree on the complete pair-score ledger")
        if any(not isinstance(score, int) or score < 0 or score > 65535 for score in scores_a):
            raise AssertionError("pair score is outside the admitted uint16 range")
        global_minimum = min(scores_a)
        if payload_a["minimum"] != global_minimum or payload_b["minimum"] != global_minimum:
            raise AssertionError("reported global minimum does not match the ledger")

        records_a = {
            tuple(record["edge_indices"]): normalized_record(record) for record in payload_a["minimizers"]
        }
        records_b = {
            tuple(record["edge_indices"]): normalized_record(record) for record in payload_b["minimizers"]
        }
        expected_minimizer_pairs = {
            pair for pair, score in zip(pairs, scores_a, strict=True) if score == global_minimum
        }
        if records_a != records_b or set(records_a) != expected_minimizer_pairs:
            raise AssertionError("independent minimizer identities disagree with the ledger")
        if any(record["total_burden"] != global_minimum for record in records_a.values()):
            raise AssertionError("minimizer identity burden does not match its ledger score")

        all_records = dict(records_a)
        slice_minimum = min(
            score
            for pair, score in zip(pairs, scores_a, strict=True)
            if eligible_deletion_remainder_change(pair, edges)
        )
        slice_minimizer_pairs = {
            pair
            for pair, score in zip(pairs, scores_a, strict=True)
            if eligible_deletion_remainder_change(pair, edges) and score == slice_minimum
        }
        for pair in sorted(slice_minimizer_pairs - set(all_records)):
            direct_a, _ = run_json(
                [sys.executable, str(checker_a), str(body1), "--pair-indices", str(pair[0]), str(pair[1])]
            )
            direct_b, _ = run_json(
                [str(checker_b), str(body1), "--pair-indices", str(pair[0]), str(pair[1])]
            )
            record_a = normalized_record(direct_a)
            record_b = normalized_record(direct_b["record"])
            if record_a != record_b or record_a["total_burden"] != scores_a[pair_to_position[pair]]:
                raise AssertionError(f"slice minimizer direct rescan mismatch at {pair}")
            all_records[pair] = record_a

        edge_index = {edge: index for index, edge in enumerate(edges)}
        control_pairs = {
            (0, 1),
            (0, EDGE_COUNT - 1),
            (1, 2),
            (EDGE_COUNT // 2, EDGE_COUNT // 2 + 1),
            (EDGE_COUNT // 2, EDGE_COUNT - 1),
            (EDGE_COUNT - 2, EDGE_COUNT - 1),
            tuple(sorted((edge_index[(6, 12)], edge_index[(9, 15)]))),
            tuple(sorted((edge_index[(33, 39)], edge_index[(36, 42)]))),
            *expected_minimizer_pairs,
            *slice_minimizer_pairs,
        }
        direct_rescans = []
        for pair in sorted(control_pairs):
            direct_a, _ = run_json(
                [sys.executable, str(checker_a), str(body1), "--pair-indices", str(pair[0]), str(pair[1])]
            )
            direct_b, _ = run_json(
                [str(checker_b), str(body1), "--pair-indices", str(pair[0]), str(pair[1])]
            )
            record_a = normalized_record(direct_a)
            record_b = normalized_record(direct_b["record"])
            expected_score = scores_a[pair_to_position[pair]]
            if record_a != record_b or record_a["total_burden"] != expected_score:
                raise AssertionError(f"direct rescan mismatch at pair {pair}")
            all_records.setdefault(pair, record_a)
            direct_rescans.append({
                "edge_indices": list(pair),
                "edges": [list(edges[pair[0]]), list(edges[pair[1]])],
                "burden": expected_score,
                "identity_agreement": True,
            })

        malformed_bytes: dict[str, bytes] = {}
        changed = bytearray(body1.read_bytes())
        first_zero = changed.find(b"0", changed.find(b"\n") + 1)
        changed[first_zero] = ord("x")
        malformed_bytes["nonbinary"] = bytes(changed)
        matrix = radius1.matrix_from_raw(body1.read_bytes())
        matrix[0][1] ^= 1
        malformed_bytes["asymmetric"] = radius1.raw_matrix_bytes(matrix)
        malformed_bytes["substituted_gist"] = (root / "inputs/k43_two_conflict_gist.txt").read_bytes()
        parser_rejections: dict[str, object] = {}
        for name, raw in malformed_bytes.items():
            path = temp / f"malformed-{name}.txt"
            path.write_bytes(raw)
            parser_rejections[name] = {
                "checker_a": expect_rejection([sys.executable, str(checker_a), str(path), "--pair-indices", "0", "1"]),
                "checker_b": expect_rejection([str(checker_b), str(path), "--pair-indices", "0", "1"]),
            }

        families = {
            "all_two_edge_flips": family_summary(
                scores_a,
                pairs,
                edges,
                lambda pair: True,
                "two distinct edges from K43",
                all_records,
            ),
            "deletion_remainder_change_for_every_valid_deletion": family_summary(
                scores_a,
                pairs,
                edges,
                lambda pair: eligible_deletion_remainder_change(pair, edges),
                "for every v in {6,12,36,42}, at least one edited edge is not incident to v",
                all_records,
            ),
        }
        expected_slice_size = PAIR_COUNT - len(INTERSECTION) * ((ORDER - 1) * (ORDER - 2) // 2)
        if families["deletion_remainder_change_for_every_valid_deletion"]["pairs"] != expected_slice_size:
            raise AssertionError("deletion-remainder-change slice cardinality mismatch")

        ledger_bytes = struct.pack(f"<{PAIR_COUNT}H", *scores_a)
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_bytes(ledger_bytes)
        ledger_sha256 = digest(ledger_path)

        report = {
            "schema_version": 1,
            "status": "publisher_seed_radius2_pass",
            "claim_scope": (
                "the frozen Springer Supplementary Data 4 K43 seed and exactly all C(903,2)=407253 "
                "two-distinct-edge flips; not a larger Hamming ball, global optimum, Ramsey witness, "
                "bound, or complete order-42 census"
            ),
            "source": {
                "authority": "Springer publisher-controlled static-content URL",
                "url": radius1.URL,
                "body_sha256": radius1.BODY_SHA256,
                "body_bytes": radius1.BODY_BYTES,
                "dual_retrieval_byte_identity": True,
                "retrievals": retrievals,
            },
            "upstream_radius1_gate": {
                "path": str(radius1_report_path),
                "sha256": digest(radius1_report_path),
                "status": radius1_report["status"],
            },
            "checker_a": {
                "path": str(checker_a),
                "sha256": digest(checker_a),
                "method": payload_a["checker"],
                "complete_ledger_seconds": elapsed_a,
            },
            "checker_b": {
                "path": str(checker_b_source),
                "source_sha256": digest(checker_b_source),
                "compiled_binary_sha256": digest(checker_b),
                "compile_command": compile_command[:-1] + ["<temporary>/publisher_radius2_b"],
                "compiler_version": subprocess.run(
                    [compiler, "--version"], text=True, capture_output=True, check=True
                ).stdout.splitlines()[0],
                "method": payload_b["checker"],
                "complete_ledger_seconds": elapsed_b,
            },
            "independence": (
                "Checker A parses the frozen spaced matrix in Python and scans each C(43,5) subset "
                "once, applying exact two-edit contribution cases. Checker B separately parses the "
                "publisher rows in C, toggles each lexicographic edge pair, and recursively enumerates "
                "graph and complement K5s afresh for every one of the 407253 edited graphs."
            ),
            "seed": {
                "order": ORDER,
                "edges": payload_a["seed_edges"],
                "zero_k5": payload_a["seed_zero_k5"],
                "one_k5": payload_a["seed_one_k5"],
                "conflict_intersection": INTERSECTION,
            },
            "complete_pair_score_ledger": {
                "path": str(ledger_path),
                "sha256": ledger_sha256,
                "bytes": len(ledger_bytes),
                "encoding": "407253 little-endian unsigned 16-bit burdens",
                "edge_order": payload_a["edge_order"],
                "pair_order": payload_a["pair_order"],
                "independent_exact_score_agreement": True,
            },
            "families": families,
            "global_minimizer_identity_agreement": True,
            "direct_rescan_controls": {
                "selection": "ledger boundaries, interior controls, the two predicted conflict-repair pairs, and every recorded minimizer",
                "count": len(direct_rescans),
                "results": direct_rescans,
            },
            "parser_rejections": parser_rejections,
            "conclusion": (
                "No distinct two-edge flip lowers the authenticated seed below burden 2. This is a "
                "complete radius-two local-isolation statement only and changes no Ramsey bound."
            ),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "report": str(output),
            "report_sha256": digest(output),
            "ledger": str(ledger_path),
            "ledger_sha256": ledger_sha256,
            "families": {
                name: {
                    "pairs": family["pairs"],
                    "minimum": family["minimum_total_burden"],
                    "minimizers": [record["edges"] for record in family["minimizers"]],
                }
                for name, family in families.items()
            },
            "direct_rescans": len(direct_rescans),
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
