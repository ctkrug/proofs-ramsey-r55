#!/usr/bin/env python3
"""Fail-closed dual-derived, proof-checked sweep of 20 R55 two-orbit slices."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str((Path(__file__).resolve().parent.parent / "checkers")))
import two_orbit_slice_a as generator_a


ORDER = 43
DISTANCES = tuple(distance for distance in range(1, 22) if distance != 6)
SOURCE_SHA256 = "c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990"
RADIUS2_SHA256 = "ee32f396c898894d32ffcbe69987caded6731f32398ce3be28cfde1d1b9c107a"
DISTANCE6_SHA256 = "8c8c64a82c84913222578fad537cc9beb73e74de5260a84090b9406f798a9fb1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, accepted=(0,), timeout=120) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.monotonic()
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    elapsed = time.monotonic() - started
    if result.returncode not in accepted:
        raise RuntimeError(
            f"command failed with {result.returncode}: {command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result, elapsed


def load_summary(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="ascii"))


def parse_ledger(path: Path):
    for line in path.read_text(encoding="ascii").splitlines():
        vertices, color, literals, fixed = line.split("|")
        yield {
            "vertices": tuple(map(int, vertices.split(","))),
            "color": int(color),
            "literals": tuple(map(int, literals.split(","))) if literals else (),
            "fixed": fixed,
        }


def frozen_orbit_value(matrix: list[list[int]], distance: int) -> int:
    word = [matrix[u][(u + distance) % ORDER] for u in range(ORDER)]
    if len(set(word)) != 1:
        raise AssertionError(f"second distance {distance} is not frozen in the publisher seed")
    return word[0]


def specialization_counter(ledger: Path, y_value: int) -> Counter[tuple[int, ...]]:
    counter: Counter[tuple[int, ...]] = Counter()
    for origin in parse_ledger(ledger):
        reduced: list[int] = []
        satisfied = False
        for literal in origin["literals"]:
            if abs(literal) <= ORDER:
                reduced.append(literal)
            else:
                literal_value = y_value if literal > 0 else 1 - y_value
                if literal_value:
                    satisfied = True
                    break
        if not satisfied:
            counter[tuple(reduced)] += 1
    return counter


def expected_distance6_counter(report: dict[str, object]) -> Counter[tuple[int, ...]]:
    reduced = report["reduced_constraint_system"]
    counter: Counter[tuple[int, ...]] = Counter()
    for pair in reduced["positive_pairs"]:
        counter[tuple(index + 1 for index in pair)] = reduced["positive_pair_multiplicity"]
    for triple in reduced["negative_triples"]:
        counter[tuple(sorted(-(index + 1) for index in triple))] = reduced["negative_triple_multiplicity"]
    return counter


def parse_model(stdout: str) -> list[int]:
    values: list[int] = []
    for line in stdout.splitlines():
        if line.startswith("v "):
            values.extend(int(token) for token in line[2:].split() if token != "0")
    assignment = [0] * (2 * ORDER)
    for literal in values:
        assignment[abs(literal) - 1] = int(literal > 0)
    if len({abs(literal) for literal in values}) != 2 * ORDER:
        raise AssertionError("SAT solver did not print a complete 86-variable model")
    return assignment


def matrix_with_assignment(base: list[list[int]], distance: int, assignment: list[int]) -> list[list[int]]:
    matrix = [row[:] for row in base]
    for u in range(ORDER):
        for offset, orbit in ((0, 6), (ORDER, distance)):
            v = (u + orbit) % ORDER
            matrix[u][v] = matrix[v][u] = assignment[offset + u]
    return matrix


def raw_matrix_bytes(matrix: list[list[int]]) -> bytes:
    rows = [generator_a.TITLE]
    rows.extend(" ".join(map(str, row)) for row in matrix)
    return ("\n".join(rows) + "\n").encode("ascii")


def rejection(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode == 0:
        raise AssertionError(f"malformed input accepted: {command}")
    return result.stderr.strip().splitlines()[-1]


def main() -> int:
    if len(sys.argv) != 12:
        raise SystemExit(
            "usage: run_two_orbit_slice_gate.py GENERATOR_A GENERATOR_B_C FULL_A FULL_B_C "
            "BODY1 BODY2 RADIUS2_REPORT DISTANCE6_REPORT DRAT_TRIM_C OUTPUT_DIR REPORT"
        )
    generator_a_path = Path(sys.argv[1]).resolve()
    generator_b_source = Path(sys.argv[2]).resolve()
    full_a = Path(sys.argv[3]).resolve()
    full_b_source = Path(sys.argv[4]).resolve()
    body1 = Path(sys.argv[5]).resolve()
    body2 = Path(sys.argv[6]).resolve()
    radius2_path = Path(sys.argv[7]).resolve()
    distance6_path = Path(sys.argv[8]).resolve()
    drat_source = Path(sys.argv[9]).resolve()
    output_dir = Path(sys.argv[10]).resolve()
    report_path = Path(sys.argv[11]).resolve()

    if output_dir.exists():
        raise ValueError("output directory already exists; use a fresh path for fail-closed replay")
    if report_path.exists():
        raise ValueError("report already exists; use a fresh path for fail-closed replay")
    if digest(body1) != SOURCE_SHA256 or digest(body2) != SOURCE_SHA256 or body1.read_bytes() != body2.read_bytes():
        raise ValueError("publisher source hash or dual-retrieval identity mismatch")
    if digest(radius2_path) != RADIUS2_SHA256:
        raise ValueError("retained radius-two gate hash mismatch")
    if digest(distance6_path) != DISTANCE6_SHA256:
        raise ValueError("retained distance-six gate hash mismatch")
    distance6_report = json.loads(distance6_path.read_text(encoding="utf-8"))
    if distance6_report.get("status") != "distance6_slice_exact_pass":
        raise ValueError("retained distance-six gate status mismatch")
    expected_specialization = expected_distance6_counter(distance6_report)
    if sum(expected_specialization.values()) != 215 or len(expected_specialization) != 129:
        raise AssertionError("retained distance-six constraint ledger has unexpected cardinality")

    compiler = shutil.which("gcc") or shutil.which("clang")
    cadical = shutil.which("cadical")
    if compiler is None or cadical is None:
        raise RuntimeError("a C compiler and CaDiCaL are required")
    output_dir.mkdir(parents=True)
    base = generator_a.parse_matrix(body1)

    with tempfile.TemporaryDirectory(prefix="r55-two-orbit-gate-") as temporary:
        temp = Path(temporary)
        generator_b = temp / "two_orbit_slice_b"
        full_b = temp / "publisher_radius1_b"
        drat_trim = temp / "drat-trim"
        compile_commands = [
            [compiler, "-std=c11", "-O3", "-Wall", "-Wextra", "-Werror", str(generator_b_source), "-o", str(generator_b)],
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(full_b_source), "-o", str(full_b)],
            [compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat_trim)],
        ]
        for command in compile_commands:
            subprocess.run(command, check=True)

        derivations: dict[int, dict[str, object]] = {}
        for distance in DISTANCES:
            slice_dir = output_dir / f"distance_{distance:02d}"
            slice_dir.mkdir()
            paths = {
                "cnf_a": slice_dir / "slice_a.cnf",
                "ledger_a": slice_dir / "origins_a.tsv",
                "summary_a": slice_dir / "summary_a.json",
                "cnf_b": slice_dir / "slice_b.cnf",
                "ledger_b": slice_dir / "origins_b.tsv",
                "summary_b": slice_dir / "summary_b.json",
            }
            _, elapsed_a = run([
                sys.executable, str(generator_a_path), str(body1), str(distance),
                str(paths["cnf_a"]), str(paths["ledger_a"]), str(paths["summary_a"]),
            ], timeout=120)
            _, elapsed_b = run([
                str(generator_b), str(body1), str(distance), str(paths["cnf_b"]),
                str(paths["ledger_b"]), str(paths["summary_b"]),
            ], timeout=120)
            summary_a = load_summary(paths["summary_a"])
            summary_b = load_summary(paths["summary_b"])
            compared_fields = (
                "order", "second_distance", "variables", "raw_active_origins", "unique_clauses",
                "all_variable_five_sets", "maximum_clause_length", "empty_clause",
            )
            if any(summary_a[field] != summary_b[field] for field in compared_fields):
                raise AssertionError(f"generator scalar mismatch at distance {distance}")
            if paths["cnf_a"].read_bytes() != paths["cnf_b"].read_bytes():
                raise AssertionError(f"generator CNF mismatch at distance {distance}")
            if paths["ledger_a"].read_bytes() != paths["ledger_b"].read_bytes():
                raise AssertionError(f"generator full-origin ledger mismatch at distance {distance}")
            y_value = frozen_orbit_value(base, distance)
            specialization = specialization_counter(paths["ledger_a"], y_value)
            if specialization != expected_specialization:
                raise AssertionError(f"distance-six specialization mismatch at distance {distance}")
            derivations[distance] = {
                "summary": {field: summary_a[field] for field in compared_fields},
                "frozen_second_orbit_value": y_value,
                "specialized_raw_origins": sum(specialization.values()),
                "specialized_unique_clauses": len(specialization),
                "cnf_sha256": digest(paths["cnf_a"]),
                "ledger_sha256": digest(paths["ledger_a"]),
                "independent_byte_identity": True,
                "seconds": {"python": elapsed_a, "c": elapsed_b},
            }

        # This mutation exercises the exact byte comparator after a plausible y-index shift.
        mutation_source = output_dir / "distance_01" / "origins_b.tsv"
        mutation = temp / "shifted-ledger.tsv"
        mutation_lines = mutation_source.read_text(encoding="ascii").splitlines()
        mutation_index = next(
            index for index, line in enumerate(mutation_lines)
            if any(abs(int(item)) > ORDER for item in line.split("|")[2].split(",") if item)
        )
        fields = mutation_lines[mutation_index].split("|")
        literals = [int(item) for item in fields[2].split(",")]
        shifted = []
        for literal in literals:
            if abs(literal) > ORDER:
                sign = 1 if literal > 0 else -1
                shifted.append(sign * (ORDER + ((abs(literal) - ORDER) % ORDER) + 1))
            else:
                shifted.append(literal)
        fields[2] = ",".join(map(str, sorted(shifted)))
        mutation_lines[mutation_index] = "|".join(fields)
        mutation.write_text("\n".join(mutation_lines) + "\n", encoding="ascii")
        if mutation.read_bytes() == mutation_source.read_bytes():
            raise AssertionError("mapping-shift mutation did not alter the ledger")

        # Structural parser controls are run through both derivations; the outer gate separately hash-locks the source.
        malformed_dir = temp / "malformed"
        malformed_dir.mkdir()
        malformed: dict[str, bytes] = {}
        nonbinary = bytearray(body1.read_bytes())
        nonbinary[nonbinary.find(b"0", nonbinary.find(b"\n") + 1)] = ord("x")
        malformed["nonbinary"] = bytes(nonbinary)
        malformed["shortened"] = body1.read_bytes()[:-2]
        asymmetric = [row[:] for row in base]
        asymmetric[0][1] ^= 1
        malformed["asymmetric"] = raw_matrix_bytes(asymmetric)
        diagonal = [row[:] for row in base]
        diagonal[0][0] = 1
        malformed["nonzero_diagonal"] = raw_matrix_bytes(diagonal)
        parser_rejections: dict[str, object] = {}
        for name, raw in malformed.items():
            path = malformed_dir / f"{name}.txt"
            path.write_bytes(raw)
            parser_rejections[name] = {
                "python": rejection([sys.executable, str(generator_a_path), str(path), "1", str(temp / "x.cnf"), str(temp / "x.tsv"), str(temp / "x.json")]),
                "c": rejection([str(generator_b), str(path), "1", str(temp / "y.cnf"), str(temp / "y.tsv"), str(temp / "y.json")]),
            }

        schedule = sorted(DISTANCES, key=lambda distance: (
            derivations[distance]["summary"]["unique_clauses"],
            derivations[distance]["summary"]["raw_active_origins"],
            distance,
        ))
        results: dict[int, dict[str, object]] = {}
        for distance in schedule:
            slice_dir = output_dir / f"distance_{distance:02d}"
            cnf = slice_dir / "slice_a.cnf"
            proof = slice_dir / "unsat.drat"
            solver_out = slice_dir / "cadical.stdout"
            solver_err = slice_dir / "cadical.stderr"
            solved, solver_seconds = run([cadical, "--quiet", str(cnf), str(proof)], accepted=(10, 20), timeout=120)
            solver_out.write_text(solved.stdout, encoding="ascii")
            solver_err.write_text(solved.stderr, encoding="ascii")
            if solved.returncode == 20:
                checked, checker_seconds = run([str(drat_trim), str(cnf), str(proof)], timeout=120)
                (slice_dir / "drat_trim.stdout").write_text(checked.stdout, encoding="ascii")
                (slice_dir / "drat_trim.stderr").write_text(checked.stderr, encoding="ascii")
                if "s VERIFIED" not in checked.stdout:
                    raise AssertionError(f"proof checker did not verify distance {distance}")
                results[distance] = {
                    "status": "unsat",
                    "solver_seconds": solver_seconds,
                    "proof_checker_seconds": checker_seconds,
                    "proof_sha256": digest(proof),
                    "proof_bytes": proof.stat().st_size,
                    "independent_drat_check": "verified",
                }
            else:
                assignment = parse_model(solved.stdout)
                candidate = matrix_with_assignment(base, distance, assignment)
                candidate_path = slice_dir / "candidate_matrix.txt"
                candidate_path.write_bytes(raw_matrix_bytes(candidate))
                checked_a, checker_a_seconds = run([sys.executable, str(full_a), "--input", str(candidate_path), "--seed-only"])
                checked_b, checker_b_seconds = run([str(full_b), "--input", str(candidate_path), "--seed-only"])
                payload_a = json.loads(checked_a.stdout)
                payload_b = json.loads(checked_b.stdout)
                identity_a = {key: sorted(payload_a["seed"][key]) for key in ("zero_k5", "one_k5")}
                identity_b = {key: sorted(payload_b["seed"][key]) for key in ("zero_k5", "one_k5")}
                if identity_a != identity_b or identity_a != {"zero_k5": [], "one_k5": []}:
                    raise AssertionError(f"SAT model failed full K5 checking at distance {distance}")
                results[distance] = {
                    "status": "sat",
                    "solver_seconds": solver_seconds,
                    "candidate_sha256": digest(candidate_path),
                    "full_k5_checkers": "both empty",
                    "checker_seconds": {"python": checker_a_seconds, "c": checker_b_seconds},
                }

        slice_manifest = []
        for distance in DISTANCES:
            slice_dir = output_dir / f"distance_{distance:02d}"
            slice_manifest.append({
                "distance": distance,
                "derivation": derivations[distance],
                "result": results[distance],
                "files": {
                    path.name: {"sha256": digest(path), "bytes": path.stat().st_size}
                    for path in sorted(slice_dir.iterdir()) if path.is_file()
                },
            })

        report = {
            "schema_version": 1,
            "status": "two_orbit_slice_gate_pass",
            "claim_scope": (
                "the union of 20 exact 86-variable slices obtained by freeing cyclic distance 6 and exactly one "
                "other cyclic-distance orbit of the authenticated Springer K43 seed; all other 19 orbits are "
                "frozen; this is not the full 903-edge space, a changed Ramsey bound, or a global optimum claim"
            ),
            "hypothesis": "at least one two-orbit slice contains a burden-zero R(5,5,43) coloring",
            "source": {"body_sha256": SOURCE_SHA256, "dual_retrieval_byte_identity": True},
            "upstream_gates": {
                "radius2": {"path": str(radius2_path), "sha256": digest(radius2_path)},
                "distance6": {"path": str(distance6_path), "sha256": digest(distance6_path)},
            },
            "encoding": {
                "variables": "1..43 are colors of {u,u+6}; 44..86 are colors of {u,u+d}, indexed by u in Z_43",
                "clauses": "for each five-set and target color, retain exactly when every fixed edge has that color; each literal forces a released edge away from the target color",
                "symmetry_breaking": "none",
                "duplicates": "full originating ledger retained; DIMACS contains sorted unique clauses because multiplicity is irrelevant to burden zero",
            },
            "derivation_independence": (
                "Python uses itertools combinations and tokenized raw parsing; C separately uses five nested loops, "
                "getline parsing, independent edge-orbit indexing, and qsort deduplication. Their complete origin "
                "ledgers and canonical CNFs agree byte-for-byte for every distance."
            ),
            "specialization_control": {
                "every_distance": True,
                "expected_raw_origins": 215,
                "expected_unique_clauses": 129,
                "comparison": "exact signed-clause Counter including multiplicity against the retained distance-6 ledger",
            },
            "schedule": schedule,
            "slices": slice_manifest,
            "controls": {
                "parser_rejections": parser_rejections,
                "mapping_shift_mutation_detected": True,
                "source_hash_locked_before_derivation": True,
            },
            "solver": {
                "path": cadical,
                "version": subprocess.run([cadical, "--version"], text=True, capture_output=True, check=True).stdout.strip(),
                "command_template": "cadical --quiet SLICE.cnf UNSAT.drat",
            },
            "proof_checker": {
                "source": str(drat_source),
                "source_sha256": digest(drat_source),
                "upstream_revision": "2e3b2dc0ecf938addbd779d42877b6ed69d9a985",
                "compiled_binary_sha256": digest(drat_trim),
                "method": "independent drat-trim backward proof checking",
            },
            "compiler": {
                "path": compiler,
                "version": subprocess.run([compiler, "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0],
                "generator_b_source_sha256": digest(generator_b_source),
                "generator_b_binary_sha256": digest(generator_b),
            },
            "result": {
                "sat_distances": [distance for distance in DISTANCES if results[distance]["status"] == "sat"],
                "unsat_distances": [distance for distance in DISTANCES if results[distance]["status"] == "unsat"],
                "all_unsat_proofs_independently_verified": all(
                    result.get("independent_drat_check") == "verified"
                    for result in results.values() if result["status"] == "unsat"
                ),
            },
            "conclusion": (
                "No burden-zero coloring exists in any proof-checked UNSAT slice. Any SAT slice is admitted only "
                "after both complete K5 checkers report no clique and no coclique. The conclusion is limited to "
                "the specified fixed-background two-orbit union."
            ),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "report": str(report_path),
            "report_sha256": digest(report_path),
            "schedule": schedule,
            "sat_distances": report["result"]["sat_distances"],
            "unsat_distances": report["result"]["unsat_distances"],
            "all_unsat_proofs_independently_verified": report["result"]["all_unsat_proofs_independently_verified"],
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
