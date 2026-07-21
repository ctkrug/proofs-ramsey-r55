#!/usr/bin/env python3
"""Independent LRAT, formula, mutation, and graph-semantic audit."""

from __future__ import annotations

import hashlib
import itertools
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
MAIN_REPORT_SHA256 = "993adc7236b0c7a241b9d17457b28e144e745e7c2d890bae17ef9c81dcbf689f"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv: list[str], *, accepted=(0,), timeout=120):
    started = time.monotonic()
    result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    elapsed = time.monotonic() - started
    if result.returncode not in accepted:
        raise RuntimeError(f"command failed: {argv}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result, elapsed


def parse_dimacs(path: Path):
    lines = path.read_text(encoding="ascii").splitlines()
    header = lines[0].split()
    if header[:2] != ["p", "cnf"] or len(header) != 4:
        raise ValueError("bad DIMACS header")
    variables, declared = map(int, header[2:])
    clauses = []
    for line in lines[1:]:
        values = tuple(map(int, line.split()))
        if not values or values[-1] != 0 or 0 in values[:-1]:
            raise ValueError("bad DIMACS clause")
        clauses.append(values[:-1])
    if len(clauses) != declared:
        raise ValueError("DIMACS clause count mismatch")
    return variables, clauses


def write_dimacs(path: Path, variables: int, clauses: list[tuple[int, ...]]) -> None:
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {variables} {len(clauses)}\n")
        for clause in clauses:
            stream.write(" ".join(map(str, clause)) + (" " if clause else "") + "0\n")


def parse_ledger(path: Path):
    origins = []
    for line in path.read_text(encoding="ascii").splitlines():
        vertices, color, literals, fixed = line.split("|")
        origins.append({
            "vertices": tuple(map(int, vertices.split(","))),
            "color": int(color),
            "literals": tuple(map(int, literals.split(","))) if literals else (),
            "fixed": fixed,
        })
    return origins


def expected_prefix(relaxations: list[int], first_aux: int):
    auxiliaries = list(range(first_aux, first_aux + len(relaxations) - 1))
    clauses = [(-relaxations[0], auxiliaries[0])]
    for index in range(1, len(relaxations) - 1):
        clauses.extend([
            (-relaxations[index], auxiliaries[index]),
            (-auxiliaries[index - 1], auxiliaries[index]),
            (-relaxations[index], -auxiliaries[index - 1]),
        ])
    clauses.append((-relaxations[-1], -auxiliaries[-1]))
    return auxiliaries[-1], clauses


def expected_suffix(relaxations: list[int], first_aux: int):
    count = len(relaxations)
    def auxiliary(position: int) -> int:
        return first_aux + position - 2
    clauses = [(-relaxations[-1], auxiliary(count))]
    for position in range(count - 1, 1, -1):
        clauses.extend([
            (-relaxations[position - 1], auxiliary(position)),
            (-auxiliary(position + 1), auxiliary(position)),
            (-relaxations[position - 1], -auxiliary(position + 1)),
        ])
    clauses.append((-relaxations[0], -auxiliary(2)))
    return auxiliary(count), clauses


def audit_formula(variables: int, clauses: list[tuple[int, ...]], origins, *, prefix: bool) -> None:
    graph_variables = 2 * ORDER
    relaxations = [graph_variables + index + 1 for index in range(len(origins))]
    origin_clauses = [origin["literals"] + (relaxations[index],) for index, origin in enumerate(origins)]
    encoder = expected_prefix if prefix else expected_suffix
    maximum, amo = encoder(relaxations, graph_variables + len(origins) + 1)
    if variables != maximum or clauses != origin_clauses + amo:
        raise AssertionError("formula/ledger/cardinality mismatch")


def must_reject(callable_) -> None:
    try:
        callable_()
    except (AssertionError, ValueError):
        return
    raise AssertionError("adversarial formula mutation was accepted")


def parse_matrix(path: Path):
    if digest(path) != SOURCE_SHA256:
        raise ValueError("source hash mismatch")
    lines = path.read_text(encoding="ascii").splitlines()
    matrix = [[int(value) for value in line.split()] for line in lines[1:]]
    if len(matrix) != ORDER or any(len(row) != ORDER for row in matrix):
        raise ValueError("matrix dimensions mismatch")
    return lines[0], matrix


def orbit_index(u: int, v: int, distance: int):
    difference = v - u
    if difference == distance:
        return u
    if difference == ORDER - distance:
        return v
    return None


def specialize(origins, matrix, distance: int) -> bytes:
    word = [matrix[u][(u + distance) % ORDER] for u in range(ORDER)]
    if len(set(word)) != 1:
        raise AssertionError("publisher second-distance orbit is not constant")
    value = word[0]
    output = []
    for origin in origins:
        reduced = []
        if any(abs(literal) > ORDER and value == int(literal > 0) for literal in origin["literals"]):
            continue
        reduced = [literal for literal in origin["literals"] if abs(literal) <= ORDER]
        fixed = []
        for u, v in itertools.combinations(origin["vertices"], 2):
            if orbit_index(u, v, 6) is None:
                fixed.append((u, v, matrix[u][v]))
        output.append(
            ",".join(map(str, origin["vertices"])) + "|" + str(origin["color"]) + "|"
            + ",".join(map(str, reduced)) + "|"
            + ",".join(f"{u}-{v}={edge}" for u, v, edge in fixed) + "\n"
        )
    return "".join(output).encode("ascii")


def patterned_assignment(distance: int):
    return (
        [int((11 * u + 5) % 17 < 8) for u in range(ORDER)]
        + [int((13 * u + 3 * distance + 7) % 19 < 9) for u in range(ORDER)]
    )


def violations(origins, assignment):
    result = {"zero_k5": [], "one_k5": []}
    for origin in origins:
        satisfied = any(assignment[abs(literal) - 1] == int(literal > 0) for literal in origin["literals"])
        if not satisfied:
            key = "zero_k5" if origin["color"] == 0 else "one_k5"
            result[key].append(list(origin["vertices"]))
    for key in result:
        result[key].sort()
    return result


def apply_assignment(base, distance: int, assignment):
    matrix = [row[:] for row in base]
    for offset, orbit in ((0, 6), (ORDER, distance)):
        for u in range(ORDER):
            v = (u + orbit) % ORDER
            matrix[u][v] = matrix[v][u] = assignment[offset + u]
    return matrix


def matrix_bytes(title: str, matrix) -> bytes:
    return (title + "\n" + "\n".join(" ".join(map(str, row)) for row in matrix) + "\n").encode("ascii")


def checker_identity(payload):
    return {key: sorted(payload["seed"][key]) for key in ("zero_k5", "one_k5")}


def test_amo_solver(cadical: str, temp: Path, variables: int, amo, relaxations, label: str):
    tests = {
        "all_false": ([-value for value in relaxations], 10),
        "first_true": ([relaxations[0]] + [-value for value in relaxations[1:]], 10),
        "middle_true": ([-value for value in relaxations] + [relaxations[len(relaxations) // 2]], 10),
        "last_true": ([-value for value in relaxations[:-1]] + [relaxations[-1]], 10),
        "first_last_true": ([relaxations[0], relaxations[-1]], 20),
    }
    result = {}
    for name, (pins, expected) in tests.items():
        # Duplicate opposite middle pin from the base all-false list is removed.
        pin_map = {abs(literal): literal for literal in pins}
        if name == "middle_true":
            pin_map[relaxations[len(relaxations) // 2]] = relaxations[len(relaxations) // 2]
        cnf = temp / f"amo-{label}-{name}.cnf"
        write_dimacs(cnf, variables, list(amo) + [(literal,) for literal in pin_map.values()])
        solved, elapsed = command([cadical, "--quiet", str(cnf)], accepted=(10, 20))
        if solved.returncode != expected:
            raise AssertionError(f"AMO semantic test failed: {label} {name}")
        result[name] = {"status": "sat" if expected == 10 else "unsat", "seconds": elapsed}
    return result


def main() -> int:
    if len(sys.argv) != 10:
        raise SystemExit(
            "usage: audit_two_orbit_burden_one.py MAIN_REPORT PACKET BODY FULL_A FULL_B_C "
            "DRAT_TRIM_C LRAT_CHECK_C LRAT_DIR OUTPUT"
        )
    main_report_path = Path(sys.argv[1]).resolve()
    packet = Path(sys.argv[2]).resolve()
    body = Path(sys.argv[3]).resolve()
    full_a = Path(sys.argv[4]).resolve()
    full_b_source = Path(sys.argv[5]).resolve()
    drat_source = Path(sys.argv[6]).resolve()
    lrat_source = Path(sys.argv[7]).resolve()
    lrat_dir = Path(sys.argv[8]).resolve()
    output = Path(sys.argv[9]).resolve()
    if digest(main_report_path) != MAIN_REPORT_SHA256:
        raise ValueError("main report hash mismatch")
    if lrat_dir.exists() or output.exists():
        raise ValueError("audit outputs already exist")
    main_report = json.loads(main_report_path.read_text(encoding="utf-8"))
    by_distance = {item["distance"]: item for item in main_report["slices"]}
    if tuple(sorted(by_distance)) != DISTANCES:
        raise AssertionError("main report does not cover the exact distance set")
    if main_report["result"]["sat_distances"] or tuple(main_report["result"]["unsat_distances"]) != DISTANCES:
        raise AssertionError("main report is not a complete UNSAT result")
    title, base = parse_matrix(body)
    compiler = shutil.which("gcc") or shutil.which("clang")
    cadical = shutil.which("cadical")
    if compiler is None or cadical is None:
        raise RuntimeError("compiler or CaDiCaL unavailable")
    lrat_dir.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="r55-burden-one-audit-") as temporary:
        temp = Path(temporary)
        drat_trim = temp / "drat-trim"
        lrat_check = temp / "lrat-check"
        full_b = temp / "full-b"
        command([compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat_trim)])
        command([compiler, "-std=c99", "-DLONGTYPE", "-O2", str(lrat_source), "-o", str(lrat_check)])
        command([compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(full_b_source), "-o", str(full_b)])

        lrat_results = {}
        semantic_results = {}
        formula_results = {}
        python_distances = {1, 3, 10, 12, 20, 21}
        single_ledger = (packet / "distance6_pilot" / "origins_a.tsv").read_bytes()
        for distance in DISTANCES:
            directory = packet / f"distance_{distance:02d}"
            recorded = by_distance[distance]
            for filename, metadata in recorded["files"].items():
                path = directory / filename
                if digest(path) != metadata["sha256"] or path.stat().st_size != metadata["bytes"]:
                    raise AssertionError(f"manifest mismatch: distance {distance} {filename}")
            origins = parse_ledger(directory / "origins_a.tsv")
            if (directory / "origins_a.tsv").read_bytes() != (directory / "origins_b.tsv").read_bytes():
                raise AssertionError("retained raw ledgers differ")
            if specialize(origins, base, distance) != single_ledger:
                raise AssertionError(f"independent specialization mismatch at distance {distance}")

            formula_entry = {}
            for label, prefix in (("a", True), ("b", False)):
                cnf = directory / f"burden_{label}.cnf"
                proof = directory / f"unsat_{label}.drat"
                variables, clauses = parse_dimacs(cnf)
                audit_formula(variables, clauses, origins, prefix=prefix)
                lrat = lrat_dir / f"distance_{distance:02d}_{label}.lrat"
                converted, conversion_seconds = command([str(drat_trim), str(cnf), str(proof), "-L", str(lrat)], timeout=600)
                checked, check_seconds = command([str(lrat_check), str(cnf), str(lrat)], timeout=600)
                if "s VERIFIED" not in converted.stdout or "c VERIFIED" not in checked.stdout:
                    raise AssertionError(f"LRAT verification failed: distance {distance} encoding {label}")
                lrat_results[f"{distance}_{label}"] = {
                    "sha256": digest(lrat), "bytes": lrat.stat().st_size,
                    "conversion_seconds": conversion_seconds, "check_seconds": check_seconds,
                    "status": "verified",
                }
                formula_entry[label] = {"variables": variables, "clauses": len(clauses), "exact_audit": True}
            formula_results[distance] = formula_entry

            assignment = patterned_assignment(distance)
            predicted = violations(origins, assignment)
            candidate = temp / f"pattern-{distance:02d}.txt"
            candidate.write_bytes(matrix_bytes(title, apply_assignment(base, distance, assignment)))
            checked_b, seconds_b = command([str(full_b), "--input", str(candidate), "--seed-only"])
            if predicted != checker_identity(json.loads(checked_b.stdout)):
                raise AssertionError(f"C full-graph semantic mismatch at distance {distance}")
            result = {
                "assignment_sha256": hashlib.sha256(bytes(assignment)).hexdigest(),
                "zero_k5": len(predicted["zero_k5"]), "one_k5": len(predicted["one_k5"]),
                "c_full_identity_agreement": True, "c_seconds": seconds_b,
            }
            if distance in python_distances:
                checked_a, seconds_a = command([sys.executable, str(full_a), "--input", str(candidate), "--seed-only"])
                if predicted != checker_identity(json.loads(checked_a.stdout)):
                    raise AssertionError(f"Python full-graph semantic mismatch at distance {distance}")
                result.update({"python_full_identity_agreement": True, "python_seconds": seconds_a})
            semantic_results[distance] = result

        # Formula mutations must be rejected by the independent exact audit.
        sentinel_dir = packet / "distance_01"
        sentinel_origins = parse_ledger(sentinel_dir / "origins_a.tsv")
        sentinel_variables, sentinel_clauses = parse_dimacs(sentinel_dir / "burden_a.cnf")
        reversed_relaxation = list(sentinel_clauses)
        reversed_relaxation[0] = reversed_relaxation[0][:-1] + (-reversed_relaxation[0][-1],)
        must_reject(lambda: audit_formula(sentinel_variables, reversed_relaxation, sentinel_origins, prefix=True))
        omitted_link = sentinel_clauses[:-1]
        must_reject(lambda: audit_formula(sentinel_variables, omitted_link, sentinel_origins, prefix=True))

        # A shifted second-orbit index must disagree with an independently materialized graph.
        baseline = violations(sentinel_origins, patterned_assignment(1))
        shifted_detected = False
        for index, origin in enumerate(sentinel_origins):
            for position, literal in enumerate(origin["literals"]):
                if abs(literal) <= ORDER:
                    continue
                shifted = [dict(item) for item in sentinel_origins]
                changed = list(origin["literals"])
                y_index = abs(literal) - ORDER - 1
                replacement = ORDER + ((y_index + 1) % ORDER) + 1
                changed[position] = replacement if literal > 0 else -replacement
                shifted[index] = dict(origin, literals=tuple(changed))
                if violations(shifted, patterned_assignment(1)) != baseline:
                    shifted_detected = True
                    break
            if shifted_detected:
                break
        if not shifted_detected:
            raise AssertionError("shifted-y-index mutation was not detected")

        unsafe = packet / "distance6_pilot" / "distance1_unsafe_deduplicated_pinned.cnf"
        unsafe_solved, unsafe_seconds = command([cadical, "--quiet", str(unsafe)], accepted=(10, 20))
        if unsafe_solved.returncode != 10:
            raise AssertionError("unsafe duplicate-merged sentinel was not SAT")
        seed_assignment = [base[u][(u + 6) % ORDER] for u in range(ORDER)] + [base[u][(u + 1) % ORDER] for u in range(ORDER)]
        seed_identity = violations(sentinel_origins, seed_assignment)
        if sum(map(len, seed_identity.values())) != 2:
            raise AssertionError("unsafe duplicate sentinel did not correspond to raw burden two")

        amo_semantics = {}
        for distance in (1, 12, 20):
            origins = parse_ledger(packet / f"distance_{distance:02d}" / "origins_a.tsv")
            relaxations = [2 * ORDER + index + 1 for index in range(len(origins))]
            for label, prefix in (("a", True), ("b", False)):
                variables, clauses = parse_dimacs(packet / f"distance_{distance:02d}" / f"burden_{label}.cnf")
                amo = clauses[len(origins):]
                amo_semantics[f"{distance}_{label}"] = test_amo_solver(
                    cadical, temp, variables, amo, relaxations, f"{distance}-{label}"
                )

        mutated_source = bytearray(body.read_bytes())
        mutated_source[-2] = ord("1") if mutated_source[-2] == ord("0") else ord("0")
        if hashlib.sha256(mutated_source).hexdigest() == SOURCE_SHA256:
            raise AssertionError("source-hash mutation control failed")

        report = {
            "schema_version": 1,
            "status": "two_orbit_burden_one_adversarial_audit_pass",
            "claim_scope": "the retained 20 raw-origin burden-at-most-one encodings, proofs, and graph mappings only",
            "main_report": {"path": str(main_report_path), "sha256": digest(main_report_path)},
            "proof_audit": {
                "method": "fresh DRAT-to-LRAT conversion followed by separately compiled lrat-check",
                "all_40_verified": True,
                "results": lrat_results,
                "drat_trim_source_sha256": digest(drat_source),
                "lrat_check_source_sha256": digest(lrat_source),
                "compiled_drat_trim_sha256": digest(drat_trim),
                "compiled_lrat_check_sha256": digest(lrat_check),
            },
            "formula_audit": {
                "method": "independently parse every CNF and require exact per-origin relaxation plus the declared prefix/suffix AMO",
                "results": formula_results,
                "reverse_relaxation_literal_rejected": True,
                "omitted_amo_link_rejected": True,
                "amo_solver_semantics": amo_semantics,
            },
            "semantic_audit": {
                "all_20_c_full_graph_identity_checks": True,
                "python_full_graph_distances": sorted(python_distances),
                "results": semantic_results,
                "all_20_independent_raw_specializations": True,
                "shifted_y_index_detected": True,
            },
            "multiplicity_control": {
                "unsafe_deduplicated_pinned_instance": str(unsafe),
                "unsafe_instance_status": "sat",
                "unsafe_solver_seconds": unsafe_seconds,
                "full_raw_seed_burden": 2,
                "duplicate_merge_error_demonstrated": True,
            },
            "source_hash_mutation_detected": True,
            "conclusion": (
                "All 40 retained UNSAT proofs pass independent LRAT checking; every extended formula matches its raw ledger; "
                "full-graph semantic checks and multiplicity/cardinality/mapping/source mutations behave as required."
            ),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"], "report": str(output), "report_sha256": digest(output),
            "lrat_proofs_verified": len(lrat_results), "semantic_slices_checked": len(semantic_results),
            "python_full_graph_distances": sorted(python_distances),
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
