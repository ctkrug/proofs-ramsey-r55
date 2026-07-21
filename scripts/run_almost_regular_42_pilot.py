#!/usr/bin/env python3
"""Fail-closed q=20 pilot for the almost-regular Ramsey(5,5,42) slice."""

from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import importlib.metadata
import io
import itertools
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "checkers"))
import almost_regular_42_cnf as encoding  # noqa: E402


CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
CORPUS_REPORT_SHA256 = "0d9b1801434edcc12f34e73cea6c98d911f0e0c6f0884f8f03d96a46eca1344c"
ORDER = 42
Q = 20


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def run(command: list[str], *, accepted: tuple[int, ...] = (0,), timeout: int = 120) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.monotonic()
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    elapsed = time.monotonic() - started
    if result.returncode not in accepted:
        raise RuntimeError(
            f"command failed ({result.returncode}): {command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result, elapsed


def parse_graph6_custom(record: bytes) -> list[int]:
    if not record or any(value < 63 or value > 126 for value in record):
        raise ValueError("invalid graph6 record")
    values = [value - 63 for value in record]
    if values[0] == 63:
        raise ValueError("only short graph6 is admitted")
    n = values[0]
    needed = (n * (n - 1) // 2 + 5) // 6
    if len(values) != needed + 1:
        raise ValueError("graph6 record length mismatch")
    bits: list[int] = []
    for value in values[1:]:
        bits.extend((value >> shift) & 1 for shift in range(5, -1, -1))
    degrees = [0] * n
    cursor = 0
    for high in range(1, n):
        for low in range(high):
            edge = bits[cursor]
            cursor += 1
            degrees[low] += edge
            degrees[high] += edge
    if any(bits[cursor:]):
        raise ValueError("nonzero graph6 padding")
    return degrees


def corpus_degree_gate(corpus: Path, retained_report: Path) -> dict[str, object]:
    if digest(corpus) != CORPUS_SHA256 or digest(retained_report) != CORPUS_REPORT_SHA256:
        raise ValueError("corpus or retained full-gate report hash mismatch")
    retained = json.loads(retained_report.read_text(encoding="utf-8"))
    if (
        retained.get("status") != "corpus_control_pass"
        or retained.get("checked_instances") != 656
        or retained.get("canonical_distinct_classes") != 656
        or retained.get("degree_range_all_656") != [19, 22]
    ):
        raise AssertionError("retained corpus gate fields changed")
    records = corpus.read_bytes().splitlines()
    if len(records) != 328 or any(not record for record in records):
        raise AssertionError("corpus record count or blank-record mismatch")
    import networkx as nx

    spreads: Counter[int] = Counter()
    degree_pairs: Counter[tuple[int, int]] = Counter()
    for record in records:
        custom = parse_graph6_custom(record)
        graph = nx.from_graph6_bytes(record)
        networkx_degrees = [degree for _, degree in graph.degree()]
        if custom != networkx_degrees or len(custom) != ORDER:
            raise AssertionError("custom/NetworkX graph6 degree disagreement")
        for degrees in (custom, [ORDER - 1 - degree for degree in custom]):
            pair = (min(degrees), max(degrees))
            degree_pairs[pair] += 1
            spreads[pair[1] - pair[0]] += 1
    if spreads != Counter({3: 656}) or degree_pairs != Counter({(19, 22): 656}):
        raise AssertionError((spreads, degree_pairs))
    return {
        "source_sha256": CORPUS_SHA256,
        "retained_full_gate_report_sha256": CORPUS_REPORT_SHA256,
        "source_records": 328,
        "source_plus_complements": 656,
        "parser_agreement": "custom-byte-parser equals NetworkX ordered degrees",
        "networkx_version": importlib.metadata.version("networkx"),
        "spread_histogram": {"3": 656},
        "min_max_histogram": {"19,22": 656},
        "almost_regular_count": 0,
        "scope": "supplied 328 records and their derived complements only; not completeness",
    }


def fixed_counter_status(cadical: str, inputs: int, q: int, mask: int, root: Path) -> bool:
    primary = list(range(1, inputs + 1))
    body = io.StringIO()
    next_variable = inputs + 1
    next_variable, first = encoding.emit_at_most(body, primary, q + 1, next_variable)
    next_variable, second = encoding.emit_at_most(body, [-value for value in primary], inputs - q, next_variable)
    units = [value if mask & (1 << (value - 1)) else -value for value in primary]
    path = root / "counter.cnf"
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"p cnf {next_variable - 1} {first + second + inputs}\n")
        stream.write(body.getvalue())
        for unit in units:
            stream.write(f"{unit} 0\n")
    result = subprocess.run([cadical, "-q", str(path)], text=True, capture_output=True)
    if result.returncode not in (10, 20):
        raise RuntimeError(f"counter solver failed: {result.returncode} {result.stderr}")
    return result.returncode == 10


def counter_and_profile_gate(cadical: str, root: Path) -> dict[str, object]:
    counter_cases = 0
    for inputs in range(1, 7):
        for q in range(inputs):
            for mask in range(1 << inputs):
                expected = mask.bit_count() in {q, q + 1}
                actual = fixed_counter_status(cadical, inputs, q, mask, root)
                counter_cases += 1
                if actual != expected:
                    raise AssertionError((inputs, q, mask, expected, actual))

    graph_cases = 0
    accepted = 0
    for n in range(1, 7):
        edges = [(u, v) for v in range(1, n) for u in range(v)]
        for mask in range(1 << len(edges)):
            degrees = [0] * n
            for index, (u, v) in enumerate(edges):
                if mask & (1 << index):
                    degrees[u] += 1
                    degrees[v] += 1
            direct = max(degrees) - min(degrees) <= 1
            branch_union = any(all(value in {q, q + 1} for value in degrees) for q in range(n))
            if direct != branch_union:
                raise AssertionError((n, mask, degrees))
            graph_cases += 1
            accepted += direct

    bands = {q: (41 - (q + 1), 41 - q) for q in range(17, 24)}
    expected_bands = {17: (23, 24), 18: (22, 23), 19: (21, 22), 20: (20, 21), 21: (19, 20), 22: (18, 19), 23: (17, 18)}
    if bands != expected_bands:
        raise AssertionError("complement band map failed")
    return {
        "counter_truth_table_cases": counter_cases,
        "counter_input_sizes": [1, 6],
        "exhaustive_graph_profile_cases": graph_cases,
        "exhaustive_graph_profile_accepted": accepted,
        "complement_band_map": {str(key): list(value) for key, value in bands.items()},
        "representative_q_values": [17, 18, 19, 20],
        "q20_self_complementary": True,
    }


def parse_model(stdout: str, primary: int) -> list[bool]:
    values: dict[int, bool] = {}
    for line in stdout.splitlines():
        if not line.startswith("v "):
            continue
        for token in line.split()[1:]:
            literal = int(token)
            if literal:
                values[abs(literal)] = literal > 0
    if any(variable not in values for variable in range(1, primary + 1)):
        raise ValueError("SAT output lacks a complete primary assignment")
    return [values[variable] for variable in range(1, primary + 1)]


def violation_scan(order: int, clique_size: int, bits: list[bool]) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    independent: list[tuple[int, ...]] = []
    cliques: list[tuple[int, ...]] = []
    for vertices in itertools.combinations(range(order), clique_size):
        values = [bits[encoding.edge_var(u, v) - 1] for u, v in itertools.combinations(vertices, 2)]
        if all(values):
            cliques.append(vertices)
        elif not any(values):
            independent.append(vertices)
    return independent, cliques


def degree_scan(order: int, bits: list[bool]) -> list[int]:
    degrees = [0] * order
    for high in range(1, order):
        for low in range(high):
            if bits[encoding.edge_var(low, high) - 1]:
                degrees[low] += 1
                degrees[high] += 1
    return degrees


def compile_tools(
    compiler: str,
    ledger_source: Path,
    checker_b_source: Path,
    drat_source: Path,
    lrat_source: Path,
    root: Path,
) -> tuple[Path, Path, Path, Path]:
    ledger = root / "ledger-b"
    checker_b = root / "checker-b"
    drat = root / "drat-trim"
    lrat = root / "lrat-check"
    run([compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(ledger_source), "-o", str(ledger)])
    run([compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)])
    run([compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat)])
    run([compiler, "-std=c99", "-DLONGTYPE", "-O2", str(lrat_source), "-o", str(lrat)])
    return ledger, checker_b, drat, lrat


def verify_lrat(drat_trim: Path, lrat_check: Path, cnf: Path, proof: Path, lrat: Path) -> dict[str, object]:
    converted, convert_seconds = run([str(drat_trim), str(cnf), str(proof), "-L", str(lrat)], timeout=600)
    checked, check_seconds = run([str(lrat_check), str(cnf), str(lrat)], timeout=600)
    if "s VERIFIED" not in converted.stdout or "c VERIFIED" not in checked.stdout:
        raise AssertionError("DRAT/LRAT verification diagnostics absent")
    return {
        "drat_sha256": digest(proof),
        "drat_bytes": proof.stat().st_size,
        "lrat_sha256": digest(lrat),
        "lrat_bytes": lrat.stat().st_size,
        "conversion_seconds": convert_seconds,
        "check_seconds": check_seconds,
    }


def r33_gate(generator: Path, ledger_b: Path, cadical: str, drat_trim: Path, lrat_check: Path, root: Path) -> dict[str, object]:
    results: dict[str, object] = {}
    for n in (5, 6):
        directory = root / f"r33-{n}"
        directory.mkdir()
        cnf, mapping, summary = directory / "r33.cnf", directory / "map.tsv", directory / "summary.json"
        run([sys.executable, str(generator), "--order", str(n), "--clique-size", "3", "--cnf", str(cnf), "--map", str(mapping), "--summary", str(summary)])
        ledger = directory / "ledger-b.txt"
        run([str(ledger_b), str(n), "3", str(ledger)])
        metadata = json.loads(summary.read_text(encoding="ascii"))
        if digest(ledger) != metadata["ramsey_ledger_sha256"]:
            raise AssertionError("R(3,3) independent ledger mismatch")
        proof = directory / "proof.drat"
        solved, seconds = run([cadical, "-q", str(cnf), str(proof)], accepted=(10, 20), timeout=60)
        if n == 5:
            if solved.returncode != 10:
                raise AssertionError("R(3,3,5) control was not SAT")
            bits = parse_model(solved.stdout, 10)
            if any(violation_scan(5, 3, bits)):
                raise AssertionError("R(3,3,5) decoded model failed")
            results["n5"] = {"status": "sat", "solver_seconds": seconds, "model_full_scan": True}
        else:
            if solved.returncode != 20:
                raise AssertionError("R(3,3,6) control was not UNSAT")
            lrat = directory / "proof.lrat"
            certificate = verify_lrat(drat_trim, lrat_check, cnf, proof, lrat)
            results["n6"] = {"status": "unsat", "solver_seconds": seconds, "certificate": certificate}
    return results


def audit_map(path: Path, order: int) -> None:
    lines = path.read_text(encoding="ascii").splitlines()
    expected = [f"{encoding.edge_var(low, high)}\t{low}\t{high}" for high in range(1, order) for low in range(high)]
    if lines != expected:
        raise AssertionError("primary variable map mismatch")


def audit_production_cnf(cnf: Path, summary: dict[str, object], ledger_sha256: str) -> dict[str, object]:
    ramsey_count = int(summary["ramsey_clauses"])
    hasher = hashlib.sha256()
    clauses = 0
    with cnf.open("rb") as stream:
        header = stream.readline().decode("ascii").split()
        if header != ["p", "cnf", str(summary["variables"]), str(summary["clauses"])]:
            raise AssertionError("DIMACS header mismatch")
        for raw in stream:
            clauses += 1
            if not raw.endswith(b" 0\n") and raw != b"0\n":
                raise AssertionError(f"malformed clause line {clauses}")
            if clauses <= ramsey_count:
                hasher.update(raw)
    if clauses != summary["clauses"] or hasher.hexdigest() != ledger_sha256:
        raise AssertionError("DIMACS count or independent Ramsey ledger mismatch")
    return {"clause_lines": clauses, "ramsey_prefix_sha256": hasher.hexdigest(), "header_exact": True}


def solver_file_limit() -> None:
    limit = 512 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))


def gzip_replace(path: Path) -> dict[str, object]:
    before = {"sha256": digest(path), "bytes": path.stat().st_size}
    destination = Path(str(path) + ".gz")
    with path.open("rb") as source, destination.open("wb") as raw_target:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_target, compresslevel=6, mtime=0) as target:
            shutil.copyfileobj(source, target, 1 << 20)
    path.unlink()
    return {**before, "gzip_path": destination.name, "gzip_sha256": digest(destination), "gzip_bytes": destination.stat().st_size}


def main() -> int:
    if len(sys.argv) != 10:
        raise SystemExit(
            "usage: run_almost_regular_42_pilot.py GENERATOR LEDGER_B_C CHECKER_B_C CORPUS CORPUS_REPORT DRAT_C LRAT_C OUTPUT_DIR REPORT"
        )
    generator, ledger_source, checker_b_source, corpus, corpus_report, drat_source, lrat_source, output_dir, report = map(
        lambda value: Path(value).resolve(), sys.argv[1:]
    )
    if output_dir.exists() or report.exists():
        raise ValueError("output directory or report already exists")
    compiler = shutil.which("gcc") or shutil.which("clang")
    cadical = shutil.which("cadical")
    labelg = shutil.which("nauty-labelg")
    complg = shutil.which("nauty-complg")
    if not all((compiler, cadical, labelg, complg)):
        raise RuntimeError("compiler, CaDiCaL, or nauty programs unavailable")
    output_dir.mkdir(parents=True)

    corpus_result = corpus_degree_gate(corpus, corpus_report)
    with tempfile.TemporaryDirectory(prefix="r55-almost-regular-") as temporary:
        temp = Path(temporary)
        ledger_b, checker_b, drat_trim, lrat_check = compile_tools(
            compiler, ledger_source, checker_b_source, drat_source, lrat_source, temp
        )
        counter_result = counter_and_profile_gate(cadical, temp)
        r33_result = r33_gate(generator, ledger_b, cadical, drat_trim, lrat_check, temp)

        cnf = output_dir / "q20.cnf"
        mapping = output_dir / "q20.map.tsv"
        summary_path = output_dir / "q20.generator.json"
        generation_started = time.monotonic()
        run([
            sys.executable, str(generator), "--order", "42", "--clique-size", "5", "--degree-q", "20",
            "--cnf", str(cnf), "--map", str(mapping), "--summary", str(summary_path),
        ], timeout=300)
        generation_seconds = time.monotonic() - generation_started
        summary = json.loads(summary_path.read_text(encoding="ascii"))
        if summary.get("degree_values") != [20, 21] or summary.get("primary_variables") != 861:
            raise AssertionError("production summary mismatch")
        audit_map(mapping, ORDER)
        ledger = temp / "q20.ramsey.ledger"
        run([str(ledger_b), "42", "5", str(ledger)], timeout=180)
        ledger_sha256 = digest(ledger)
        if ledger_sha256 != summary["ramsey_ledger_sha256"]:
            raise AssertionError("Python/C production Ramsey ledger mismatch")
        cnf_audit = audit_production_cnf(cnf, summary, ledger_sha256)

        # Executed mutation sentinels: each changes an independently locked observable.
        first_ledger_line = ledger.read_bytes().splitlines(keepends=True)[0]
        mutated_literal = first_ledger_line.replace(b"1 ", b"-1 ", 1)
        correct_degrees = degree_scan(4, [True, False, False, False, False, False])
        shifted_degrees = degree_scan(4, [False, True, False, False, False, False])
        map_lines = mapping.read_text(encoding="ascii").splitlines()
        corrupted_map_lines = map_lines[:]
        corrupted_map_lines[0] = "1\t0\t2"
        mutation_results = {
            "omitted_ramsey_clause_detected_by_count": int(summary["clauses"]) - 1 != cnf_audit["clause_lines"],
            "negated_ramsey_literal_detected_by_ledger_hash": hashlib.sha256(mutated_literal).digest() != hashlib.sha256(first_ledger_line).digest(),
            "shifted_incidence_detected": correct_degrees != shifted_degrees,
            "weakened_bound_detected_by_truth_table": (3 not in {1, 2}) and (3 in {1, 2, 3}),
            "corrupt_map_detected": corrupted_map_lines != map_lines,
        }
        if not all(mutation_results.values()):
            raise AssertionError("mutation sentinel failed")

        proof = output_dir / "q20.partial-or-final.drat"
        solver_started = time.monotonic()
        solved = subprocess.run(
            [cadical, "-q", "-t", "300", str(cnf), str(proof)],
            text=True,
            capture_output=True,
            preexec_fn=solver_file_limit,
        )
        solver_seconds = time.monotonic() - solver_started
        (output_dir / "cadical.stdout").write_text(solved.stdout, encoding="ascii")
        (output_dir / "cadical.stderr").write_text(solved.stderr, encoding="ascii")
        result: dict[str, object]
        lrat_metadata: dict[str, object] | None = None
        model_metadata: dict[str, object] | None = None
        if solved.returncode == 10:
            bits = parse_model(solved.stdout, 861)
            independent, cliques = violation_scan(ORDER, 5, bits)
            degrees = degree_scan(ORDER, bits)
            if independent or cliques or not all(degree in {20, 21} for degree in degrees):
                raise AssertionError("production SAT model failed direct scan")
            padded = bits + [False] * ((-len(bits)) % 6)
            graph6 = bytes([ORDER + 63] + [
                63 + sum((1 if padded[offset + index] else 0) << (5 - index) for index in range(6))
                for offset in range(0, len(padded), 6)
            ]) + b"\n"
            model_path = output_dir / "q20.model.g6"
            model_path.write_bytes(graph6)
            checked_c, _ = run([str(checker_b), "--format", "graph6", "--input", str(model_path)], timeout=120)
            c_payload = json.loads(checked_c.stdout)["graphs"][0]
            if c_payload["zero_k5"] or c_payload["one_k5"] or c_payload["degrees"] != degrees:
                raise AssertionError("C recursive-bitset model scan disagreed")
            complements = temp / "corpus-complements.g6"
            canonical_corpus = temp / "corpus-canonical.g6"
            combined = temp / "corpus-combined.g6"
            canonical_model = output_dir / "q20.model.canonical.g6"
            run([complg, "-q", str(corpus), str(complements)])
            combined.write_bytes(corpus.read_bytes() + complements.read_bytes())
            run([labelg, "-q", str(combined), str(canonical_corpus)])
            run([labelg, "-q", str(model_path), str(canonical_model)])
            novel_to_supplied = canonical_model.read_bytes().strip() not in set(canonical_corpus.read_bytes().splitlines())
            if not novel_to_supplied:
                raise AssertionError("almost-regular model unexpectedly matched supplied corpus")
            model_metadata = {
                "primary_assignment_sha256": hashlib.sha256(bytes(bits)).hexdigest(),
                "degree_histogram": dict(sorted(Counter(degrees).items())),
                "python_full_scan": True,
                "c_recursive_bitset_full_scan": True,
                "nauty_canonical_novel_to_supplied_656": novel_to_supplied,
            }
            result = {"status": "sat", "scope": "q=20 degree band only"}
        elif solved.returncode == 20:
            lrat = output_dir / "q20.lrat"
            lrat_metadata = verify_lrat(drat_trim, lrat_check, cnf, proof, lrat)
            result = {"status": "unsat_verified", "scope": "q=20 degree band only"}
        else:
            result = {
                "status": "unknown",
                "scope": "q=20 degree band only",
                "returncode": solved.returncode,
                "timed_out": solved.returncode == 0,
                "proof_file_limit_bytes": 512 * 1024 * 1024,
                "qualification": "no exclusion; any partial proof is not a certificate",
            }

        cnf_storage = gzip_replace(cnf)
        proof_storage = gzip_replace(proof) if proof.exists() else None
        if (output_dir / "q20.lrat").exists():
            gzip_replace(output_dir / "q20.lrat")

        payload = {
            "schema_version": 1,
            "status": "almost_regular_42_q20_pilot_complete",
            "scope": "Ramsey(5,5,42) graphs with every degree in {20,21}; no symmetry breaking",
            "source_status": "43 <= R(5,5) <= 46 as checked against DS1.18 revision 18",
            "corpus_gate": corpus_result,
            "counter_and_profile_gate": counter_result,
            "r33_control": r33_result,
            "production": {
                "generator_summary": summary,
                "generation_seconds": generation_seconds,
                "cnf_audit": cnf_audit,
                "cnf_storage": cnf_storage,
                "proof_storage": proof_storage,
                "solver": {
                    "path": cadical,
                    "version": subprocess.run([cadical, "--version"], text=True, capture_output=True).stdout.strip(),
                    "command": [cadical, "-q", "-t", "300", "q20.cnf", "q20.partial-or-final.drat"],
                    "wall_seconds": solver_seconds,
                    "returncode": solved.returncode,
                },
                "result": result,
                "lrat_metadata": lrat_metadata,
                "model_metadata": model_metadata,
            },
            "independence": {
                "python_generator": digest(generator),
                "c_nested_loop_ledger_source": digest(ledger_source),
                "ramsey_ledger_byte_hash_agreement": True,
                "degree_semantics": "CaDiCaL truth table on every 1..6-bit row and every q",
                "profile_semantics": "all labeled graphs through order 6",
            },
            "mutation_sentinels": mutation_results,
            "tool_versions": {
                "python": sys.version.split()[0],
                "compiler": subprocess.run([compiler, "--version"], text=True, capture_output=True).stdout.splitlines()[0],
                "networkx": importlib.metadata.version("networkx"),
                "cadical": subprocess.run([cadical, "--version"], text=True, capture_output=True).stdout.strip(),
                "nauty_labelg": labelg,
                "nauty_complg": complg,
            },
            "conclusion": (
                "A checked SAT model would establish a supplied-corpus-novel almost-regular order-42 graph; "
                "a verified UNSAT result would exclude only q=20; unknown changes no mathematical bound."
            ),
        }
        report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": payload["status"],
            "report": str(report),
            "report_sha256": digest(report),
            "production_result": result,
            "cnf_clauses": summary["clauses"],
            "cnf_variables": summary["variables"],
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
