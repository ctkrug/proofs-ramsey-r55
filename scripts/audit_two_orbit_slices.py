#!/usr/bin/env python3
"""Adversarial LRAT and full-graph semantic audit of the two-orbit sweep."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ORDER = 43
DISTANCES = tuple(distance for distance in range(1, 22) if distance != 6)
SOURCE_SHA256 = "c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990"
MAIN_REPORT_SHA256 = "0456c5764898ab28d248d20912f26fd6708cac5d283151e1673110ce73690627"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv: list[str], timeout=120) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.monotonic()
    result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    elapsed = time.monotonic() - started
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {argv}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result, elapsed


def parse_matrix(path: Path) -> list[list[int]]:
    raw = path.read_bytes()
    if digest(path) != SOURCE_SHA256:
        raise ValueError("source hash mismatch")
    lines = raw.decode("ascii").splitlines()
    if len(lines) != ORDER + 1:
        raise ValueError("source row count mismatch")
    matrix = [[int(token) for token in line.split()] for line in lines[1:]]
    if any(len(row) != ORDER for row in matrix):
        raise ValueError("source width mismatch")
    return matrix


def raw_matrix_bytes(matrix: list[list[int]], title: str) -> bytes:
    return (title + "\n" + "\n".join(" ".join(map(str, row)) for row in matrix) + "\n").encode("ascii")


def ledger_violations(path: Path, assignment: list[int]) -> dict[str, list[list[int]]]:
    result = {"zero_k5": [], "one_k5": []}
    for line in path.read_text(encoding="ascii").splitlines():
        vertices, color_text, literal_text, _fixed = line.split("|")
        literals = [int(item) for item in literal_text.split(",")] if literal_text else []
        satisfied = any(assignment[abs(literal) - 1] == int(literal > 0) for literal in literals)
        if not satisfied:
            key = "zero_k5" if int(color_text) == 0 else "one_k5"
            result[key].append([int(item) for item in vertices.split(",")])
    for key in result:
        result[key].sort()
    return result


def seed_assignment(matrix: list[list[int]], distance: int) -> list[int]:
    return (
        [matrix[u][(u + 6) % ORDER] for u in range(ORDER)]
        + [matrix[u][(u + distance) % ORDER] for u in range(ORDER)]
    )


def patterned_assignment(distance: int) -> list[int]:
    # Fixed arithmetic pattern, not generated from the slice clauses.
    return (
        [int((7 * u + 3) % 11 < 5) for u in range(ORDER)]
        + [int((5 * u + 2 * distance + 1) % 13 < 6) for u in range(ORDER)]
    )


def apply_assignment(base: list[list[int]], distance: int, assignment: list[int]) -> list[list[int]]:
    matrix = [row[:] for row in base]
    for u, value in enumerate(assignment[:ORDER]):
        v = (u + 6) % ORDER
        matrix[min(u, v)][max(u, v)] = value
        matrix[max(u, v)][min(u, v)] = value
    for u, value in enumerate(assignment[ORDER:]):
        v = (u + distance) % ORDER
        matrix[min(u, v)][max(u, v)] = value
        matrix[max(u, v)][min(u, v)] = value
    return matrix


def checker_identity(payload: dict[str, object]) -> dict[str, list[list[int]]]:
    return {key: sorted(payload["seed"][key]) for key in ("zero_k5", "one_k5")}


def main() -> int:
    if len(sys.argv) != 10:
        raise SystemExit(
            "usage: audit_two_orbit_slices.py MAIN_REPORT SLICE_DIR BODY FULL_A FULL_B_C "
            "DRAT_TRIM_C LRAT_CHECK_C LRAT_DIR OUTPUT"
        )
    main_report_path = Path(sys.argv[1]).resolve()
    slices = Path(sys.argv[2]).resolve()
    body = Path(sys.argv[3]).resolve()
    full_a = Path(sys.argv[4]).resolve()
    full_b_source = Path(sys.argv[5]).resolve()
    drat_source = Path(sys.argv[6]).resolve()
    lrat_source = Path(sys.argv[7]).resolve()
    lrat_dir = Path(sys.argv[8]).resolve()
    output = Path(sys.argv[9]).resolve()
    if digest(main_report_path) != MAIN_REPORT_SHA256:
        raise ValueError("main two-orbit report hash mismatch")
    if lrat_dir.exists() or output.exists():
        raise ValueError("audit outputs already exist; use fresh paths")
    main_report = json.loads(main_report_path.read_text(encoding="utf-8"))
    by_distance = {item["distance"]: item for item in main_report["slices"]}
    if tuple(sorted(by_distance)) != DISTANCES:
        raise AssertionError("main report does not cover the exact 20-distance set")
    if main_report["result"]["sat_distances"] or tuple(main_report["result"]["unsat_distances"]) != DISTANCES:
        raise AssertionError("main report result is not the expected complete UNSAT sweep")
    base = parse_matrix(body)
    title = body.read_text(encoding="ascii").splitlines()[0]
    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise RuntimeError("C compiler unavailable")
    lrat_dir.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="r55-two-orbit-audit-") as temporary:
        temp = Path(temporary)
        drat_trim = temp / "drat-trim"
        lrat_check = temp / "lrat-check"
        full_b = temp / "full-b"
        subprocess.run([compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat_trim)], check=True)
        subprocess.run([compiler, "-std=c99", "-DLONGTYPE", "-O2", str(lrat_source), "-o", str(lrat_check)], check=True)
        subprocess.run([compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(full_b_source), "-o", str(full_b)], check=True)

        lrat_results: dict[int, object] = {}
        semantic_results: dict[int, object] = {}
        seed_identity: dict[str, list[list[int]]] | None = None
        python_full_distances = {1, 3, 10, 20, 21}
        for distance in DISTANCES:
            slice_dir = slices / f"distance_{distance:02d}"
            cnf = slice_dir / "slice_a.cnf"
            proof = slice_dir / "unsat.drat"
            ledger = slice_dir / "origins_a.tsv"
            recorded = by_distance[distance]
            for filename, path in (("slice_a.cnf", cnf), ("unsat.drat", proof), ("origins_a.tsv", ledger)):
                if digest(path) != recorded["files"][filename]["sha256"]:
                    raise AssertionError(f"retained file hash mismatch: distance {distance} {filename}")
            lrat = lrat_dir / f"distance_{distance:02d}.lrat"
            converted, convert_seconds = command([str(drat_trim), str(cnf), str(proof), "-L", str(lrat)])
            checked, check_seconds = command([str(lrat_check), str(cnf), str(lrat)])
            if "s VERIFIED" not in converted.stdout or "c VERIFIED" not in checked.stdout:
                raise AssertionError(f"LRAT conversion/check failed at distance {distance}")
            lrat_results[distance] = {
                "sha256": digest(lrat), "bytes": lrat.stat().st_size,
                "drat_to_lrat_seconds": convert_seconds, "lrat_check_seconds": check_seconds,
                "lrat_check": "verified",
            }

            seed_predicted = ledger_violations(ledger, seed_assignment(base, distance))
            if seed_identity is None:
                seed_path = temp / "seed.txt"
                seed_path.write_bytes(raw_matrix_bytes(base, title))
                checked_seed, _ = command([str(full_b), "--input", str(seed_path), "--seed-only"])
                seed_identity = checker_identity(json.loads(checked_seed.stdout))
            if seed_predicted != seed_identity:
                raise AssertionError(f"seed semantic mismatch at distance {distance}")

            assignment = patterned_assignment(distance)
            predicted = ledger_violations(ledger, assignment)
            candidate_path = temp / f"pattern-{distance:02d}.txt"
            candidate_path.write_bytes(raw_matrix_bytes(apply_assignment(base, distance, assignment), title))
            checked_b, elapsed_b = command([str(full_b), "--input", str(candidate_path), "--seed-only"])
            identity_b = checker_identity(json.loads(checked_b.stdout))
            if predicted != identity_b:
                raise AssertionError(f"C full-graph semantic mismatch at distance {distance}")
            result = {
                "pattern_assignment_sha256": hashlib.sha256(bytes(assignment)).hexdigest(),
                "zero_k5": len(predicted["zero_k5"]), "one_k5": len(predicted["one_k5"]),
                "c_full_checker_seconds": elapsed_b, "c_full_identity_agreement": True,
                "seed_identity_agreement": True,
            }
            if distance in python_full_distances:
                checked_a, elapsed_a = command([sys.executable, str(full_a), "--input", str(candidate_path), "--seed-only"])
                identity_a = checker_identity(json.loads(checked_a.stdout))
                if predicted != identity_a:
                    raise AssertionError(f"Python full-graph semantic mismatch at distance {distance}")
                result.update({"python_full_checker_seconds": elapsed_a, "python_full_identity_agreement": True})
            semantic_results[distance] = result

        report = {
            "schema_version": 1,
            "status": "two_orbit_slice_adversarial_audit_pass",
            "claim_scope": "the retained 20 two-orbit CNFs/proofs and their declared variable-to-edge mapping only",
            "main_report": {"path": str(main_report_path), "sha256": digest(main_report_path)},
            "proof_audit": {
                "method": "convert each archived binary DRAT proof to textual LRAT, then check with separately compiled lrat-check",
                "drat_trim_source_sha256": digest(drat_source),
                "lrat_check_source_sha256": digest(lrat_source),
                "compiled_drat_trim_sha256": digest(drat_trim),
                "compiled_lrat_check_sha256": digest(lrat_check),
                "all_verified": True,
                "results": lrat_results,
            },
            "semantic_audit": {
                "method": (
                    "evaluate every full origin ledger on the publisher assignment and on a fixed arithmetic 86-bit "
                    "pattern, materialize the corresponding 43x43 graph independently, and compare exact K5 identity lists"
                ),
                "seed_identity": seed_identity,
                "all_20_checked_with_c_full_enumerator": True,
                "python_full_enumerator_distances": sorted(python_full_distances),
                "results": semantic_results,
            },
            "conclusion": (
                "Every archived UNSAT proof also passes an LRAT check, and every slice's declared mapping agrees with "
                "a full graph/complement K5 enumeration on an independent patterned assignment plus the seed assignment."
            ),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"], "report": str(output), "report_sha256": digest(output),
            "lrat_proofs_verified": len(lrat_results), "semantic_slices_checked": len(semantic_results),
            "python_full_enumerator_distances": sorted(python_full_distances),
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
