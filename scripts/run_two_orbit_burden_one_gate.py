#!/usr/bin/env python3
"""Fail-closed proof-carrying burden-at-most-one sweep of R55 orbit slices."""

from __future__ import annotations

from collections import Counter
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
ZERO_REPORT_SHA256 = "0456c5764898ab28d248d20912f26fd6708cac5d283151e1673110ce73690627"
ZERO_AUDIT_SHA256 = "38f2b91ca963760dc1fed0107be7fef0c40d41d3fd7da2a7104103447c6b36c8"
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


def parse_matrix(path: Path) -> list[list[int]]:
    if digest(path) != SOURCE_SHA256:
        raise ValueError("publisher source hash mismatch")
    lines = path.read_text(encoding="ascii").splitlines()
    if len(lines) != ORDER + 1:
        raise ValueError("publisher matrix row count mismatch")
    matrix = [[int(token) for token in line.split()] for line in lines[1:]]
    if any(len(row) != ORDER for row in matrix):
        raise ValueError("publisher matrix width mismatch")
    return matrix


def orbit_index(u: int, v: int, distance: int) -> int | None:
    difference = v - u
    if difference == distance:
        return u
    if difference == ORDER - distance:
        return v
    return None


def parse_ledger(path: Path):
    for line in path.read_text(encoding="ascii").splitlines():
        vertices, color, literals, fixed = line.split("|")
        yield {
            "vertices": tuple(map(int, vertices.split(","))),
            "color": int(color),
            "literals": tuple(map(int, literals.split(","))) if literals else (),
            "fixed": fixed,
        }


def ledger_line(vertices: tuple[int, ...], color: int, literals: tuple[int, ...],
                fixed: list[tuple[int, int, int]]) -> str:
    return (
        ",".join(map(str, vertices)) + "|" + str(color) + "|"
        + ",".join(map(str, literals)) + "|"
        + ",".join(f"{u}-{v}={value}" for u, v, value in fixed) + "\n"
    )


def specialized_ledger(path: Path, matrix: list[list[int]], distance: int) -> bytes:
    orbit_word = [matrix[u][(u + distance) % ORDER] for u in range(ORDER)]
    if len(set(orbit_word)) != 1:
        raise AssertionError(f"distance {distance} is not constant in publisher matrix")
    value = orbit_word[0]
    output: list[str] = []
    for origin in parse_ledger(path):
        reduced: list[int] = []
        satisfied = False
        for literal in origin["literals"]:
            if abs(literal) <= ORDER:
                reduced.append(literal)
            elif value == int(literal > 0):
                satisfied = True
                break
        if satisfied:
            continue
        fixed: list[tuple[int, int, int]] = []
        for u, v in itertools.combinations(origin["vertices"], 2):
            if orbit_index(u, v, 6) is None:
                fixed.append((u, v, matrix[u][v]))
        output.append(ledger_line(origin["vertices"], origin["color"], tuple(reduced), fixed))
    return "".join(output).encode("ascii")


def parse_dimacs(path: Path) -> tuple[int, list[tuple[int, ...]]]:
    lines = path.read_text(encoding="ascii").splitlines()
    header = lines[0].split()
    if len(header) != 4 or header[:2] != ["p", "cnf"]:
        raise ValueError("invalid DIMACS header")
    variables, declared = map(int, header[2:])
    clauses: list[tuple[int, ...]] = []
    for line in lines[1:]:
        tokens = list(map(int, line.split()))
        if not tokens or tokens[-1] != 0 or 0 in tokens[:-1]:
            raise ValueError("invalid DIMACS clause")
        clauses.append(tuple(tokens[:-1]))
    if len(clauses) != declared:
        raise ValueError("DIMACS clause count mismatch")
    return variables, clauses


def write_dimacs(path: Path, variables: int, clauses: list[tuple[int, ...]]) -> None:
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {variables} {len(clauses)}\n")
        for clause in clauses:
            stream.write(" ".join(map(str, clause)) + (" " if clause else "") + "0\n")


def prefix_amo(relaxations: list[int], first_auxiliary: int) -> tuple[int, list[tuple[int, ...]]]:
    if len(relaxations) <= 1:
        return first_auxiliary - 1, []
    auxiliaries = list(range(first_auxiliary, first_auxiliary + len(relaxations) - 1))
    clauses = [(-relaxations[0], auxiliaries[0])]
    for index in range(1, len(relaxations) - 1):
        clauses.extend((
            (-relaxations[index], auxiliaries[index]),
            (-auxiliaries[index - 1], auxiliaries[index]),
            (-relaxations[index], -auxiliaries[index - 1]),
        ))
    clauses.append((-relaxations[-1], -auxiliaries[-1]))
    return auxiliaries[-1], clauses


def suffix_amo(relaxations: list[int], first_auxiliary: int) -> tuple[int, list[tuple[int, ...]]]:
    if len(relaxations) <= 1:
        return first_auxiliary - 1, []
    # t_i, i=2..m, occupies first_auxiliary+i-2.
    def auxiliary(position: int) -> int:
        return first_auxiliary + position - 2
    count = len(relaxations)
    clauses: list[tuple[int, ...]] = [(-relaxations[-1], auxiliary(count))]
    for position in range(count - 1, 1, -1):
        clauses.extend((
            (-relaxations[position - 1], auxiliary(position)),
            (-auxiliary(position + 1), auxiliary(position)),
            (-relaxations[position - 1], -auxiliary(position + 1)),
        ))
    clauses.append((-relaxations[0], -auxiliary(2)))
    return auxiliary(count), clauses


def sequential_at_most_k(relaxations: list[int], bound: int, first_auxiliary: int,
                         *, reverse: bool = False) -> tuple[int, list[tuple[int, ...]]]:
    xs = list(reversed(relaxations)) if reverse else list(relaxations)
    count = len(xs)
    if bound >= count:
        return first_auxiliary - 1, []
    auxiliaries = {
        (position, level): first_auxiliary + (position - 1) * bound + level - 1
        for position in range(1, count) for level in range(1, bound + 1)
    }
    clauses: list[tuple[int, ...]] = []
    for position in range(1, count):
        clauses.append((-xs[position - 1], auxiliaries[position, 1]))
    for position in range(2, count):
        clauses.append((-auxiliaries[position - 1, 1], auxiliaries[position, 1]))
    for level in range(2, bound + 1):
        for position in range(2, count):
            clauses.append((-xs[position - 1], -auxiliaries[position - 1, level - 1], auxiliaries[position, level]))
            clauses.append((-auxiliaries[position - 1, level], auxiliaries[position, level]))
    for position in range(2, count + 1):
        clauses.append((-xs[position - 1], -auxiliaries[position - 1, bound]))
    return max(auxiliaries.values()), clauses


def exact_formula_audit(cnf: Path, ledger: Path, graph_variables: int, *, prefix: bool) -> None:
    variables, clauses = parse_dimacs(cnf)
    origins = list(parse_ledger(ledger))
    count = len(origins)
    relaxations = [graph_variables + index + 1 for index in range(count)]
    expected_origins = [origin["literals"] + (relaxations[index],) for index, origin in enumerate(origins)]
    encoder = prefix_amo if prefix else suffix_amo
    expected_max, expected_amo = encoder(relaxations, graph_variables + count + 1)
    if variables != expected_max or clauses != expected_origins + expected_amo:
        raise AssertionError("extended CNF does not exactly match its raw ledger and declared AMO")


def append_pins(source: Path, target: Path, pins: list[int]) -> None:
    variables, clauses = parse_dimacs(source)
    write_dimacs(target, variables, clauses + [(literal,) for literal in pins])


def solve_and_check(cadical: str, drat_trim: Path, cnf: Path, proof: Path, *, timeout: int) -> dict[str, object]:
    solved, solver_seconds = run([cadical, "--quiet", str(cnf), str(proof)], accepted=(10, 20), timeout=timeout)
    result: dict[str, object] = {
        "status": "sat" if solved.returncode == 10 else "unsat",
        "solver_seconds": solver_seconds,
        "solver_stdout": solved.stdout,
        "solver_stderr": solved.stderr,
    }
    if solved.returncode == 20:
        checked, checker_seconds = run([str(drat_trim), str(cnf), str(proof)], timeout=timeout)
        if "s VERIFIED" not in checked.stdout:
            raise AssertionError(f"DRAT proof did not verify for {cnf}")
        result.update({
            "proof_checker_seconds": checker_seconds,
            "proof_sha256": digest(proof),
            "proof_bytes": proof.stat().st_size,
            "independent_drat_check": "verified",
        })
    return result


def model_values(stdout: str) -> dict[int, int]:
    values: dict[int, int] = {}
    for line in stdout.splitlines():
        if line.startswith("v "):
            for literal in map(int, line[2:].split()):
                if literal:
                    values[abs(literal)] = int(literal > 0)
    return values


def assignment_for_mode(matrix: list[list[int]], mode: int) -> list[int]:
    assignment = [matrix[u][(u + 6) % ORDER] for u in range(ORDER)]
    if mode:
        assignment.extend(matrix[u][(u + mode) % ORDER] for u in range(ORDER))
    return assignment


def ledger_violations(path: Path, assignment: list[int]) -> dict[str, list[list[int]]]:
    result = {"zero_k5": [], "one_k5": []}
    for origin in parse_ledger(path):
        if not any(assignment[abs(literal) - 1] == int(literal > 0) for literal in origin["literals"]):
            key = "zero_k5" if origin["color"] == 0 else "one_k5"
            result[key].append(list(origin["vertices"]))
    for key in result:
        result[key].sort()
    return result


def checker_identity(payload: dict[str, object]) -> dict[str, list[list[int]]]:
    return {key: sorted(payload["seed"][key]) for key in ("zero_k5", "one_k5")}


def build_pinned_bound_two(ledger: Path, assignment: list[int], output: Path, *, reverse: bool) -> None:
    origins = list(parse_ledger(ledger))
    graph_variables = len(assignment)
    relaxations = [graph_variables + index + 1 for index in range(len(origins))]
    relaxed = [origin["literals"] + (relaxations[index],) for index, origin in enumerate(origins)]
    maximum, cardinality = sequential_at_most_k(
        relaxations, 2, graph_variables + len(origins) + 1, reverse=reverse
    )
    pins = [(index + 1 if value else -(index + 1),) for index, value in enumerate(assignment)]
    write_dimacs(output, maximum, relaxed + cardinality + pins)


def build_unsafe_deduplicated_pinned(ledger: Path, assignment: list[int], output: Path) -> None:
    unique = sorted({origin["literals"] for origin in parse_ledger(ledger)})
    graph_variables = len(assignment)
    relaxations = [graph_variables + index + 1 for index in range(len(unique))]
    relaxed = [clause + (relaxations[index],) for index, clause in enumerate(unique)]
    maximum, amo = prefix_amo(relaxations, graph_variables + len(unique) + 1)
    pins = [(index + 1 if value else -(index + 1),) for index, value in enumerate(assignment)]
    write_dimacs(output, maximum, relaxed + amo + pins)


def matrix_bytes(matrix: list[list[int]], title: str) -> bytes:
    return (title + "\n" + "\n".join(" ".join(map(str, row)) for row in matrix) + "\n").encode("ascii")


def matrix_with_assignment(base: list[list[int]], distance: int, assignment: list[int]) -> list[list[int]]:
    matrix = [row[:] for row in base]
    for offset, orbit in ((0, 6), (ORDER, distance)):
        for u in range(ORDER):
            v = (u + orbit) % ORDER
            matrix[u][v] = matrix[v][u] = assignment[offset + u]
    return matrix


def main() -> int:
    if len(sys.argv) != 13:
        raise SystemExit(
            "usage: run_two_orbit_burden_one_gate.py GENERATOR_A GENERATOR_B_C FULL_A FULL_B_C "
            "BODY1 BODY2 ZERO_REPORT ZERO_AUDIT DISTANCE6_REPORT DRAT_TRIM_C OUTPUT_DIR REPORT"
        )
    generator_a = Path(sys.argv[1]).resolve()
    generator_b_source = Path(sys.argv[2]).resolve()
    full_a = Path(sys.argv[3]).resolve()
    full_b_source = Path(sys.argv[4]).resolve()
    body1 = Path(sys.argv[5]).resolve()
    body2 = Path(sys.argv[6]).resolve()
    zero_report = Path(sys.argv[7]).resolve()
    zero_audit = Path(sys.argv[8]).resolve()
    distance6_report = Path(sys.argv[9]).resolve()
    drat_source = Path(sys.argv[10]).resolve()
    output_dir = Path(sys.argv[11]).resolve()
    report_path = Path(sys.argv[12]).resolve()
    if output_dir.exists() or report_path.exists():
        raise ValueError("output packet or report already exists; use fresh paths")
    locks = {
        body1: SOURCE_SHA256, body2: SOURCE_SHA256,
        zero_report: ZERO_REPORT_SHA256, zero_audit: ZERO_AUDIT_SHA256,
        distance6_report: DISTANCE6_SHA256,
    }
    for path, expected in locks.items():
        if digest(path) != expected:
            raise ValueError(f"hash lock failed for {path}")
    if body1.read_bytes() != body2.read_bytes():
        raise AssertionError("publisher retrievals differ")
    matrix = parse_matrix(body1)
    title = body1.read_text(encoding="ascii").splitlines()[0]
    compiler = shutil.which("gcc") or shutil.which("clang")
    cadical = shutil.which("cadical")
    if compiler is None or cadical is None:
        raise RuntimeError("compiler or CaDiCaL unavailable")
    output_dir.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="r55-burden-one-") as temporary:
        temp = Path(temporary)
        generator_b = temp / "generator-b"
        full_b = temp / "full-b"
        drat_trim = temp / "drat-trim"
        run([compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(generator_b_source), "-o", str(generator_b)])
        run([compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(full_b_source), "-o", str(full_b)])
        run([compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat_trim)])

        def generate(mode: int, directory: Path) -> tuple[dict[str, object], dict[str, object]]:
            directory.mkdir(parents=True)
            paths_a = [directory / name for name in ("burden_a.cnf", "origins_a.tsv", "mapping_a.tsv", "summary_a.json")]
            paths_b = [directory / name for name in ("burden_b.cnf", "origins_b.tsv", "mapping_b.tsv", "summary_b.json")]
            run([sys.executable, str(generator_a), str(body1), str(mode), *map(str, paths_a)])
            run([str(generator_b), str(body1), str(mode), *map(str, paths_b)])
            if paths_a[1].read_bytes() != paths_b[1].read_bytes():
                raise AssertionError(f"raw-origin ledger mismatch in mode {mode}")
            if paths_a[2].read_bytes() != paths_b[2].read_bytes():
                raise AssertionError(f"origin-relaxation mapping mismatch in mode {mode}")
            summary_a = json.loads(paths_a[3].read_text(encoding="ascii"))
            summary_b = json.loads(paths_b[3].read_text(encoding="ascii"))
            comparable = set(summary_a) - {"checker", "cardinality_encoding"}
            if {key: summary_a[key] for key in comparable} != {key: summary_b[key] for key in comparable}:
                raise AssertionError(f"extended encoding size mismatch in mode {mode}")
            exact_formula_audit(paths_a[0], paths_a[1], summary_a["graph_variables"], prefix=True)
            exact_formula_audit(paths_b[0], paths_b[1], summary_b["graph_variables"], prefix=False)
            return summary_a, summary_b

        pilot_dir = output_dir / "distance6_pilot"
        pilot_a, pilot_b = generate(0, pilot_dir)
        if pilot_a["raw_active_origins"] != 215 or pilot_a["graph_variables"] != 43:
            raise AssertionError("one-orbit raw-origin pilot did not reproduce 215 origins")
        pilot_results: dict[str, object] = {}
        for label in ("a", "b"):
            cnf = pilot_dir / f"burden_{label}.cnf"
            proof = pilot_dir / f"unsat_{label}.drat"
            result = solve_and_check(cadical, drat_trim, cnf, proof, timeout=120)
            (pilot_dir / f"cadical_{label}.stdout").write_text(result.pop("solver_stdout"), encoding="ascii")
            (pilot_dir / f"cadical_{label}.stderr").write_text(result.pop("solver_stderr"), encoding="ascii")
            if result["status"] != "unsat":
                raise AssertionError("known distance-6 burden-at-most-one pilot was not UNSAT")
            pilot_results[label] = result

        derivations: dict[int, object] = {}
        single_ledger = (pilot_dir / "origins_a.tsv").read_bytes()
        for distance in DISTANCES:
            directory = output_dir / f"distance_{distance:02d}"
            summary_a, summary_b = generate(distance, directory)
            prior_ledger = Path("artifacts/two_orbit_slices") / f"distance_{distance:02d}" / "origins_a.tsv"
            if (directory / "origins_a.tsv").read_bytes() != prior_ledger.read_bytes():
                raise AssertionError(f"new raw ledger does not reproduce burden-zero ledger at distance {distance}")
            projected = specialized_ledger(directory / "origins_a.tsv", matrix, distance)
            (directory / "specialized_to_distance6.tsv").write_bytes(projected)
            if projected != single_ledger:
                raise AssertionError(f"raw-origin specialization mismatch at distance {distance}")
            derivations[distance] = {
                "raw_active_origins": summary_a["raw_active_origins"],
                "variables": summary_a["variables"],
                "clauses": summary_a["clauses"],
                "ledger_sha256": digest(directory / "origins_a.tsv"),
                "mapping_sha256": digest(directory / "mapping_a.tsv"),
                "python_c_raw_ledger_byte_identity": True,
                "python_c_origin_mapping_byte_identity": True,
                "exact_extended_formula_audits": True,
                "specialization_raw_ledger_identity": True,
                "prior_burden_zero_ledger_identity": True,
            }

        duplicate_clause = (7, 37)
        distance1_origins = list(parse_ledger(output_dir / "distance_01" / "origins_a.tsv"))
        duplicates = [origin for origin in distance1_origins if origin["literals"] == duplicate_clause]
        if len(duplicates) != 2 or [origin["vertices"] for origin in duplicates] != [
            (6, 12, 17, 36, 42), (6, 12, 31, 36, 42)
        ]:
            raise AssertionError("distance-1 duplicate-origin sentinel missing")

        seed_assignment = assignment_for_mode(matrix, 1)
        seed_identity = ledger_violations(output_dir / "distance_01" / "origins_a.tsv", seed_assignment)
        seed_file = pilot_dir / "publisher_seed.txt"
        seed_file.write_bytes(matrix_bytes(matrix, title))
        full_a_result, _ = run([sys.executable, str(full_a), "--input", str(seed_file), "--seed-only"])
        full_b_result, _ = run([str(full_b), "--input", str(seed_file), "--seed-only"])
        if seed_identity != checker_identity(json.loads(full_a_result.stdout)) or seed_identity != checker_identity(json.loads(full_b_result.stdout)):
            raise AssertionError("raw ledger does not reproduce full publisher-seed K5 identities")
        if sum(map(len, seed_identity.values())) != 2:
            raise AssertionError("publisher seed does not have exactly two raw violations")

        pinned_results: dict[str, object] = {}
        pins = [index + 1 if value else -(index + 1) for index, value in enumerate(seed_assignment)]
        for label in ("a", "b"):
            pinned = pilot_dir / f"distance1_pinned_le1_{label}.cnf"
            append_pins(output_dir / "distance_01" / f"burden_{label}.cnf", pinned, pins)
            proof = pilot_dir / f"distance1_pinned_le1_{label}.drat"
            result = solve_and_check(cadical, drat_trim, pinned, proof, timeout=120)
            result.pop("solver_stdout")
            result.pop("solver_stderr")
            if result["status"] != "unsat":
                raise AssertionError("pinned burden-at-most-one control was not UNSAT")
            pinned_results[f"le1_{label}"] = result
        for label, reverse in (("prefix", False), ("reversed", True)):
            bound_two = pilot_dir / f"distance1_pinned_le2_{label}.cnf"
            build_pinned_bound_two(output_dir / "distance_01" / "origins_a.tsv", seed_assignment, bound_two, reverse=reverse)
            proof = pilot_dir / f"distance1_pinned_le2_{label}.proof"
            result = solve_and_check(cadical, drat_trim, bound_two, proof, timeout=120)
            if result["status"] != "sat":
                raise AssertionError("pinned burden-at-most-two positive control was not SAT")
            values = model_values(result["solver_stdout"])
            violated_indices = [
                index + 1 for index, origin in enumerate(distance1_origins)
                if not any(seed_assignment[abs(literal) - 1] == int(literal > 0) for literal in origin["literals"])
            ]
            relaxations = [2 * ORDER + index for index in violated_indices]
            if any(values.get(variable) != 1 for variable in relaxations):
                raise AssertionError("bound-two model did not relax both violated raw origins")
            result.pop("solver_stdout")
            result.pop("solver_stderr")
            pinned_results[f"le2_{label}"] = result

        unsafe = pilot_dir / "distance1_unsafe_deduplicated_pinned.cnf"
        build_unsafe_deduplicated_pinned(output_dir / "distance_01" / "origins_a.tsv", seed_assignment, unsafe)
        unsafe_result, _ = run([cadical, "--quiet", str(unsafe)], accepted=(10, 20), timeout=120)
        if unsafe_result.returncode != 10:
            raise AssertionError("duplicate-merge sentinel did not expose the expected false burden-one result")

        remaining = [distance for distance in DISTANCES if distance not in {1, 12, 20}]
        schedule = [1, 12, 20] + sorted(remaining, key=lambda distance: (derivations[distance]["raw_active_origins"], distance))
        results: dict[int, object] = {}
        for distance in schedule:
            directory = output_dir / f"distance_{distance:02d}"
            per_encoding: dict[str, object] = {}
            for label in ("a", "b"):
                cnf = directory / f"burden_{label}.cnf"
                proof = directory / f"unsat_{label}.drat"
                result = solve_and_check(cadical, drat_trim, cnf, proof, timeout=600)
                (directory / f"cadical_{label}.stdout").write_text(result.pop("solver_stdout"), encoding="ascii")
                (directory / f"cadical_{label}.stderr").write_text(result.pop("solver_stderr"), encoding="ascii")
                per_encoding[label] = result
            statuses = {result["status"] for result in per_encoding.values()}
            if len(statuses) != 1:
                raise AssertionError(f"independent encoding SAT-status mismatch at distance {distance}")
            status = statuses.pop()
            if status == "sat":
                for label in ("a", "b"):
                    stdout = (directory / f"cadical_{label}.stdout").read_text(encoding="ascii")
                    values = model_values(stdout)
                    assignment = [values[index + 1] for index in range(2 * ORDER)]
                    predicted = ledger_violations(directory / "origins_a.tsv", assignment)
                    candidate = matrix_with_assignment(matrix, distance, assignment)
                    candidate_path = directory / f"candidate_{label}.txt"
                    candidate_path.write_bytes(matrix_bytes(candidate, title))
                    checked_a, _ = run([sys.executable, str(full_a), "--input", str(candidate_path), "--seed-only"])
                    checked_b, _ = run([str(full_b), "--input", str(candidate_path), "--seed-only"])
                    if predicted != checker_identity(json.loads(checked_a.stdout)) or predicted != checker_identity(json.loads(checked_b.stdout)):
                        raise AssertionError(f"SAT model semantic mismatch at distance {distance}")
                    if sum(map(len, predicted.values())) > 1:
                        raise AssertionError(f"SAT model exceeds raw burden one at distance {distance}")
            results[distance] = {"status": status, "encodings": per_encoding}

        manifest: list[dict[str, object]] = []
        for distance in DISTANCES:
            directory = output_dir / f"distance_{distance:02d}"
            manifest.append({
                "distance": distance,
                "derivation": derivations[distance],
                "result": results[distance],
                "files": {
                    path.name: {"sha256": digest(path), "bytes": path.stat().st_size}
                    for path in sorted(directory.iterdir()) if path.is_file()
                },
            })
        report = {
            "schema_version": 1,
            "status": "two_orbit_burden_one_gate_pass",
            "claim_scope": (
                "raw monochromatic-K5 burden at most one in the 20 fixed-background slices freeing cyclic distance 6 "
                "and one other distance; no symmetry reduction; not the full graph space or a changed Ramsey bound"
            ),
            "hypothesis": "at least one retained two-orbit slice has raw monochromatic-K5 burden at most one",
            "source": {"body_sha256": SOURCE_SHA256, "dual_retrieval_byte_identity": True},
            "upstream_hash_locks": {str(path): expected for path, expected in locks.items()},
            "encoding": {
                "graph_variables": "1..43 encode distance 6; 44..86 encode the second distance",
                "raw_origin_relaxation": "one distinct positive relaxation variable per five-set/color origin, before deduplication",
                "python_cardinality": "prefix sequential AMO",
                "c_cardinality": "independently emitted suffix sequential AMO",
                "symmetry_breaking": "none",
            },
            "pilot": {
                "distance6_raw_origins": pilot_a["raw_active_origins"],
                "results": pilot_results,
                "raw_ledger_byte_identity": True,
                "mapping_byte_identity": True,
            },
            "controls": {
                "all_20_specialize_to_exact_215-origin_distance6_ledger": True,
                "all_20_reproduce_prior_raw_ledgers": True,
                "distance1_duplicate_clause": list(duplicate_clause),
                "distance1_duplicate_vertices": [list(origin["vertices"]) for origin in duplicates],
                "publisher_seed_identity": seed_identity,
                "publisher_seed_full_checker_agreement": True,
                "pinned_cardinality_results": pinned_results,
                "unsafe_duplicate_merge_spuriously_sat": True,
                "exact_formula_audit_both_encodings": True,
            },
            "schedule": schedule,
            "slices": manifest,
            "solver": {
                "path": cadical,
                "version": run([cadical, "--version"])[0].stdout.strip(),
            },
            "proof_checker": {
                "source": str(drat_source),
                "source_sha256": digest(drat_source),
                "compiled_binary_sha256": digest(drat_trim),
                "upstream_revision": "2e3b2dc0ecf938addbd779d42877b6ed69d9a985",
                "method": "freshly compiled drat-trim checks every UNSAT encoding",
            },
            "compiler": {
                "path": compiler,
                "version": run([compiler, "--version"])[0].stdout.splitlines()[0],
                "generator_b_source_sha256": digest(generator_b_source),
                "generator_b_binary_sha256": digest(generator_b),
            },
            "result": {
                "sat_distances": [distance for distance in DISTANCES if results[distance]["status"] == "sat"],
                "unsat_distances": [distance for distance in DISTANCES if results[distance]["status"] == "unsat"],
                "dual_drat_checks": sum(
                    result.get("independent_drat_check") == "verified"
                    for item in results.values() for result in item["encodings"].values()
                ),
            },
        }
        if not report["result"]["sat_distances"] and tuple(report["result"]["unsat_distances"]) == DISTANCES:
            report["conclusion"] = (
                "Every slice is burden-at-most-one UNSAT under both independently derived raw-origin encodings. "
                "Together with the publisher assignment of burden two, every specified slice has exact minimum burden two."
            )
        else:
            report["conclusion"] = (
                "Each listed SAT distance has a decoded graph of raw burden at most one checked by two full K5 enumerators; "
                "each listed UNSAT distance has two independently checked DRAT proofs."
            )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "report": str(report_path),
            "report_sha256": digest(report_path),
            "schedule": schedule,
            "sat_distances": report["result"]["sat_distances"],
            "unsat_distances": report["result"]["unsat_distances"],
            "dual_drat_checks": report["result"]["dual_drat_checks"],
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
