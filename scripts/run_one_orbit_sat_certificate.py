#!/usr/bin/env python3
"""Certify the complete distance-six optimum classification with CNF/DRAT."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


N = 43
TITLE = "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def file_record(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def parse_matrix(path: Path) -> list[list[int]]:
    lines = path.read_text(encoding="ascii").splitlines()
    if len(lines) != N + 1 or lines[0] != TITLE:
        raise ValueError("matrix title or row count mismatch")
    matrix = [[int(field) for field in line.split()] for line in lines[1:]]
    if any(len(row) != N for row in matrix):
        raise ValueError("matrix width mismatch")
    for u in range(N):
        if matrix[u][u] != 0:
            raise ValueError("nonzero diagonal")
        for v in range(u + 1, N):
            if matrix[u][v] != matrix[v][u]:
                raise ValueError("asymmetric matrix")
    return matrix


def matrix_bytes(matrix: list[list[int]]) -> bytes:
    return (TITLE + "\n" + "\n".join(" ".join(map(str, row)) for row in matrix) + "\n").encode("ascii")


def matrix_for_word(base: list[list[int]], word: str) -> list[list[int]]:
    result = [row[:] for row in base]
    for u, bit in enumerate(word):
        v = (u + 6) % N
        result[u][v] = result[v][u] = int(bit)
    return result


def exhaustive_identities(matrix: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    rows = [sum(matrix[u][v] << v for v in range(N)) for u in range(N)]
    zero: list[list[int]] = []
    one: list[list[int]] = []
    for vertices in itertools.combinations(range(N), 5):
        mask = sum(1 << vertex for vertex in vertices)
        twice_edges = sum((rows[vertex] & mask).bit_count() for vertex in vertices)
        if twice_edges == 0:
            zero.append(list(vertices))
        elif twice_edges == 20:
            one.append(list(vertices))
    return zero, one


def interval_class(word: str) -> str | None:
    transformed = [word[(27 * t) % N] for t in range(N)]
    transitions = sum(transformed[index] != transformed[(index + 1) % N] for index in range(N))
    ones = transformed.count("1")
    if transitions == 2 and ones in {24, 25}:
        return f"step27_cyclic_interval_length_{ones}"
    return None


def generate(
    generator: Path,
    matrix: Path,
    cnf: Path,
    metadata: Path,
    maximum: int,
    encoding: str,
    block_words: Path | None = None,
) -> None:
    command = [
        sys.executable,
        str(generator),
        str(matrix),
        str(cnf),
        str(metadata),
        "--distances",
        "6",
        "--max-burden",
        str(maximum),
        "--cardinality-encoding",
        encoding,
    ]
    if block_words is not None:
        command.extend(["--block-words", str(block_words)])
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def unsat_certificate(cadical: Path, drat_trim: Path, cnf: Path, proof: Path, solver_log: Path, checker_log: Path) -> dict[str, object]:
    if proof.exists():
        proof.unlink()
    started = time.monotonic()
    solver = subprocess.run([str(cadical), "-q", "-n", str(cnf), str(proof)], text=True, capture_output=True)
    solver_log.write_text(solver.stdout + solver.stderr, encoding="utf-8")
    if solver.returncode != 20 or "s UNSATISFIABLE" not in solver.stdout:
        raise AssertionError(f"CaDiCaL did not prove UNSAT for {cnf.name}")
    solver_seconds = time.monotonic() - started
    started = time.monotonic()
    checker = subprocess.run([str(drat_trim), str(cnf), str(proof)], text=True, capture_output=True)
    checker_log.write_text(checker.stdout + checker.stderr, encoding="utf-8")
    if checker.returncode != 0 or "s VERIFIED" not in checker.stdout:
        raise AssertionError(f"drat-trim did not verify {proof.name}")
    return {
        "cnf": file_record(cnf),
        "proof": file_record(proof),
        "solver_log": file_record(solver_log),
        "checker_log": file_record(checker_log),
        "solver_seconds": round(solver_seconds, 6),
        "checker_seconds": round(time.monotonic() - started, 6),
        "solver_returncode": solver.returncode,
        "checker_returncode": checker.returncode,
        "checker_verdict": "VERIFIED",
    }


def parse_dimacs(path: Path) -> tuple[int, list[list[int]]]:
    variable_count = -1
    clauses: list[list[int]] = []
    for line in path.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("c"):
            continue
        if line.startswith("p cnf "):
            _, _, variables, expected_clauses = line.split()
            variable_count = int(variables)
            expected = int(expected_clauses)
            continue
        literals = [int(item) for item in line.split()]
        if not literals or literals[-1] != 0:
            raise ValueError("malformed DIMACS clause")
        clauses.append(literals[:-1])
    if variable_count < 0 or len(clauses) != expected:
        raise ValueError("DIMACS header mismatch")
    return variable_count, clauses


def write_dimacs(path: Path, variable_count: int, clauses: list[list[int]]) -> None:
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {variable_count} {len(clauses)}\n")
        for clause in clauses:
            stream.write(" ".join(map(str, clause)) + (" " if clause else "") + "0\n")


def solve_sat(cadical: Path, cnf: Path) -> str | None:
    result = subprocess.run([str(cadical), "--sat", "-q", str(cnf)], text=True, capture_output=True)
    if result.returncode == 20:
        if "s UNSATISFIABLE" not in result.stdout:
            raise AssertionError("UNSAT exit without verdict")
        return None
    if result.returncode != 10 or "s SATISFIABLE" not in result.stdout:
        raise AssertionError("unexpected SAT solver result")
    assignments: dict[int, bool] = {}
    for line in result.stdout.splitlines():
        if not line.startswith("v "):
            continue
        for literal_text in line[2:].split():
            literal = int(literal_text)
            if literal:
                assignments[abs(literal)] = literal > 0
    if any(variable not in assignments for variable in range(1, N + 1)):
        raise AssertionError("SAT witness omits a base variable")
    return "".join("1" if assignments[variable] else "0" for variable in range(1, N + 1))


def main() -> int:
    if len(sys.argv) != 10:
        raise SystemExit(
            "usage: run_one_orbit_sat_certificate.py GENERATOR BITSET_CPP MATRIX RETAINED_REPORT "
            "CADICAL DRAT_TRIM ARTIFACT_DIR OUTPUT_REPORT MODELS_OUTPUT"
        )
    generator, bitset_cpp, matrix_path, retained_path, cadical, drat_trim, artifact_dir, output_report, models_output = map(Path, sys.argv[1:])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    base = parse_matrix(matrix_path)
    compiler = shutil.which("clang++") or shutil.which("g++")
    if compiler is None:
        raise RuntimeError("a C++20 compiler is required")
    started = time.monotonic()

    certificates: dict[str, object] = {}
    for maximum in (0, 1):
        stem = artifact_dir / f"distance6-burden{maximum}"
        cnf = stem.with_suffix(".cnf")
        metadata = stem.with_suffix(".metadata.json")
        proof = stem.with_suffix(".drat")
        solver_log = stem.with_suffix(".solver.log")
        checker_log = stem.with_suffix(".checker.log")
        generate(generator, matrix_path, cnf, metadata, maximum, "combinatorial")
        certificate = unsat_certificate(cadical, drat_trim, cnf, proof, solver_log, checker_log)
        certificate["metadata"] = file_record(metadata)
        certificate["metadata_summary"] = json.loads(metadata.read_text(encoding="utf-8"))
        certificates[f"burden_at_most_{maximum}"] = certificate

    with tempfile.TemporaryDirectory(prefix="r55-one-orbit-enumeration-") as temporary_name:
        temporary = Path(temporary_name)
        sequential_cnf = temporary / "burden2-sequential.cnf"
        sequential_metadata = temporary / "burden2-sequential.metadata.json"
        generate(generator, matrix_path, sequential_cnf, sequential_metadata, 2, "sequential")
        variable_count, base_clauses = parse_dimacs(sequential_cnf)
        search_clauses = list(base_clauses)
        discovered: set[str] = set()
        for iteration in range(1, 1000):
            current = temporary / "enumeration.cnf"
            write_dimacs(current, variable_count, search_clauses)
            word = solve_sat(cadical, current)
            if word is None:
                break
            if word in discovered:
                raise AssertionError("blocking clause failed to remove a model")
            discovered.add(word)
            search_clauses.append([-(index + 1) if bit == "1" else index + 1 for index, bit in enumerate(word)])
        else:
            raise AssertionError("model enumeration did not terminate")

        bitset_executable = temporary / "adversarial_radius2_bitset"
        subprocess.run(
            [compiler, "-std=c++20", "-O3", "-Wall", "-Wextra", "-Werror", str(bitset_cpp), "-o", str(bitset_executable)],
            check=True,
        )
        validations: list[dict[str, object]] = []
        classification = Counter()
        for index, word in enumerate(sorted(discovered)):
            matrix = matrix_for_word(base, word)
            zero, one = exhaustive_identities(matrix)
            candidate_path = temporary / f"model-{index:03d}.txt"
            candidate_path.write_bytes(matrix_bytes(matrix))
            bitset_result = subprocess.run([str(bitset_executable), str(candidate_path)], text=True, capture_output=True, check=True)
            bitset = json.loads(bitset_result.stdout)
            if bitset["zero_k5"] != len(zero) or bitset["one_k5"] != len(one):
                raise AssertionError("the two full K5 checkers disagree on an optimum model")
            if len(zero) + len(one) != 2:
                raise AssertionError("enumerated model does not have burden two")
            label = interval_class(word)
            if label is None:
                raise AssertionError("enumerated model lies outside the interval classification")
            classification[label] += 1
            validations.append({
                "word_u_order": word,
                "class": label,
                "zero_k5": zero,
                "one_k5": one,
                "python_exhaustive_and_cpp_bitset_agree": True,
            })

    words = sorted(discovered)
    if len(words) != 86 or classification != Counter({
        "step27_cyclic_interval_length_24": 43,
        "step27_cyclic_interval_length_25": 43,
    }):
        raise AssertionError("independent optimum enumeration or classification mismatch")
    retained = json.loads(retained_path.read_text(encoding="utf-8"))["exact_result"]["minimum_words_u_order"]
    if words != sorted(retained):
        raise AssertionError("independent optimum model set differs from the retained set")
    models_output.write_text(json.dumps(words, indent=2) + "\n", encoding="utf-8")

    final_cnf = artifact_dir / "distance6-burden2-exhausted.cnf"
    final_metadata = artifact_dir / "distance6-burden2-exhausted.metadata.json"
    final_proof = artifact_dir / "distance6-burden2-exhausted.drat"
    final_solver_log = artifact_dir / "distance6-burden2-exhausted.solver.log"
    final_checker_log = artifact_dir / "distance6-burden2-exhausted.checker.log"
    generate(generator, matrix_path, final_cnf, final_metadata, 2, "combinatorial", models_output)
    final_certificate = unsat_certificate(
        cadical, drat_trim, final_cnf, final_proof, final_solver_log, final_checker_log
    )
    final_certificate["metadata"] = file_record(final_metadata)
    final_certificate["metadata_summary"] = json.loads(final_metadata.read_text(encoding="utf-8"))
    certificates["burden_at_most_2_after_blocking_all_86_models"] = final_certificate

    report = {
        "schema_version": 1,
        "status": "distance6_independent_cnf_drat_classification_pass",
        "claim_scope": "All 2^43 assignments to the distance-six orbit with every other orbit frozen to the authenticated Springer matrix.",
        "result": {
            "burden_at_most": {"0": "UNSAT", "1": "UNSAT", "2": "SAT"},
            "minimum_burden": 2,
            "minimum_model_count": len(words),
            "classification": dict(sorted(classification.items())),
            "complete_model_set_matches_retained_report": True,
            "each_model_validated_by_two_full_graph_checkers": True,
        },
        "models": file_record(models_output),
        "model_validations": validations,
        "certificates": certificates,
        "tools": {
            "cadical": {
                "path": str(cadical),
                "sha256": digest(cadical),
                "version": subprocess.run([str(cadical), "--version"], text=True, capture_output=True, check=True).stdout.strip(),
            },
            "drat_trim": {"path": str(drat_trim), "sha256": digest(drat_trim)},
            "generator": file_record(generator),
            "bitset_checker": file_record(bitset_cpp),
        },
        "independence": "The deterministic DIMACS was generated from all C(43,5) five-sets without retained code; direct combinatorial cardinality clauses were used in every certified formula; CaDiCaL emitted proof logs checked by drat-trim; every decoded optimum was rescanned by exhaustive Python induced-edge counts and the separate C++ bitset triangle/common-neighborhood checker.",
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    output_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "models": len(words),
        "classification": report["result"]["classification"],
        "output": str(output_report),
        "output_sha256": digest(output_report),
        "elapsed_seconds": report["elapsed_seconds"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
