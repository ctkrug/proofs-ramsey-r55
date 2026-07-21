#!/usr/bin/env python3
"""Proof-carrying 16-cube pilot for the normalized q=20 R(5,5,42) CNF."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from typing import BinaryIO


ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "retained_q20_runner", ROOT / "scripts" / "run_almost_regular_42_pilot.py"
)
if BASE_SPEC is None or BASE_SPEC.loader is None:
    raise RuntimeError("cannot load retained exact model scanners")
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)


EXPECTED_Q20_SHA256 = "87b70753dd07b3fc04ddb62799701a8a379efb2cd5c9ea9ddbd026f6679865dd"
EXPECTED_Q20_GZIP_SHA256 = "edc51d7e497a9d6da452800fb5ac09742d1b4db7db516d2ba4c673dda55dbfea"
EXPECTED_Q20_MAP_SHA256 = "dc65a8e25bd320154c0c2dea86cc29b3e33ce5bc73979ab6dc7555265074fc9d"
EXPECTED_Q20_VARIABLES = 71421
EXPECTED_Q20_CLAUSES = 1844093
PROOF_LIMIT_BYTES = 64 * 1024 * 1024
AGGREGATE_STORAGE_LIMIT = 256 * 1024 * 1024


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def open_binary(path: Path) -> BinaryIO:
    return gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")


def edge_variable(u: int, v: int) -> int:
    low, high = sorted((u, v))
    if low == high:
        raise ValueError("loop")
    return high * (high - 1) // 2 + low + 1


def run(
    command: list[str],
    *,
    accepted: tuple[int, ...] = (0,),
    timeout: int = 120,
    preexec_fn=None,
) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.monotonic()
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=timeout,
        preexec_fn=preexec_fn,
    )
    elapsed = time.monotonic() - started
    if result.returncode not in accepted:
        raise RuntimeError(
            f"command failed ({result.returncode}): {command}\n{result.stdout}\n{result.stderr}"
        )
    return result, elapsed


def read_parent(path: Path) -> tuple[bytes, int, int, bytes, str, str]:
    whole = hashlib.sha256()
    body_hash = hashlib.sha256()
    with open_binary(path) as stream:
        header = stream.readline()
        fields = header.decode("ascii").split()
        if len(fields) != 4 or fields[:2] != ["p", "cnf"]:
            raise AssertionError("bad parent header")
        variables, clauses = map(int, fields[2:])
        whole.update(header)
        body_parts: list[bytes] = []
        count = 0
        for line in stream:
            whole.update(line)
            body_hash.update(line)
            body_parts.append(line)
            count += 1
    if count != clauses:
        raise AssertionError("parent clause count mismatch")
    return header, variables, clauses, b"".join(body_parts), whole.hexdigest(), body_hash.hexdigest()


def path_orbits() -> list[list[str]]:
    unseen = {"".join(map(str, bits)) for bits in itertools.product((0, 1), repeat=4)}
    classes: list[list[str]] = []
    while unseen:
        word = min(unseen)
        orbit = sorted({word, word[::-1]})
        classes.append(orbit)
        unseen.difference_update(orbit)
    return classes


def build_manifest(
    parent_path: Path,
    map_path: Path,
    order: int,
    degree_q: int,
    edges: list[list[int]],
    scope: str,
    destination: Path,
) -> dict[str, object]:
    _, variables, clauses, body, whole_sha256, body_sha256 = read_parent(parent_path)
    path_variables = [edge_variable(*edge) for edge in edges]
    leaves: list[dict[str, object]] = []
    new_header = f"p cnf {variables} {clauses + 4}\n".encode("ascii")
    for bits in itertools.product((0, 1), repeat=4):
        leaf_id = "".join(map(str, bits))
        literals = [variable if bit else -variable for bit, variable in zip(bits, path_variables)]
        suffix = b"".join(f"{literal} 0\n".encode("ascii") for literal in literals)
        leaf_hasher = hashlib.sha256()
        leaf_hasher.update(new_header)
        leaf_hasher.update(body)
        leaf_hasher.update(suffix)
        leaves.append(
            {
                "id": leaf_id,
                "bits": list(bits),
                "literals": literals,
                "clauses": clauses + 4,
                "suffix_sha256": hashlib.sha256(suffix).hexdigest(),
                "leaf_uncompressed_sha256": leaf_hasher.hexdigest(),
            }
        )
    payload: dict[str, object] = {
        "schema_version": 1,
        "scope": scope,
        "order": order,
        "degree_q": degree_q,
        "fixed_root": 0,
        "left_part": list(range(1, degree_q + 1)),
        "right_part": list(range(degree_q + 1, order)),
        "path_edges": edges,
        "path_variables": path_variables,
        "path_reversal_orbit_classes": path_orbits(),
        "parent": {
            "path": str(parent_path.relative_to(ROOT)) if parent_path.is_relative_to(ROOT) else str(parent_path),
            "variables": variables,
            "clauses": clauses,
            "uncompressed_sha256": whole_sha256,
            "compressed_sha256": digest(parent_path) if parent_path.suffix == ".gz" else None,
            "body_sha256": body_sha256,
            "map_sha256": digest(map_path),
        },
        "cover_contract": "all 2^4 assignments in lexicographic bit order; no symmetry quotient",
        "physical_leaf_contract": "replace parent header clause count by parent+4 and append four unit clauses",
        "leaves": leaves,
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def materialize_leaf(parent: Path, leaf: dict[str, object], destination: Path) -> None:
    with open_binary(parent) as source, destination.open("wb") as target:
        fields = source.readline().decode("ascii").split()
        variables, clauses = map(int, fields[2:])
        target.write(f"p cnf {variables} {clauses + 4}\n".encode("ascii"))
        shutil.copyfileobj(source, target, 1 << 20)
        for literal in leaf["literals"]:
            target.write(f"{literal} 0\n".encode("ascii"))
    if digest(destination) != leaf["leaf_uncompressed_sha256"]:
        raise AssertionError("materialized leaf differs from manifest hash")


def proof_file_limit() -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE, (PROOF_LIMIT_BYTES, PROOF_LIMIT_BYTES))


def compile_tools(compiler: str, drat_source: Path, lrat_source: Path, checker_b_source: Path, root: Path):
    drat = root / "drat-trim"
    lrat = root / "lrat-check"
    checker_b = root / "checker-b"
    run([compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat)])
    run([compiler, "-std=c99", "-DLONGTYPE", "-O2", str(lrat_source), "-o", str(lrat)])
    run([compiler, "-std=c11", "-O2", str(checker_b_source), "-o", str(checker_b)])
    return drat, lrat, checker_b


def verify_certificate(drat: Path, lrat_check: Path, cnf: Path, proof: Path, lrat: Path) -> dict[str, object]:
    converted, convert_seconds = run([str(drat), str(cnf), str(proof), "-L", str(lrat)], timeout=600)
    checked, check_seconds = run([str(lrat_check), str(cnf), str(lrat)], timeout=600)
    return {
        "target_cnf_sha256": digest(cnf),
        "drat_sha256": digest(proof),
        "drat_bytes": proof.stat().st_size,
        "lrat_sha256": digest(lrat),
        "lrat_bytes": lrat.stat().st_size,
        "drat_to_lrat_returncode": converted.returncode,
        "drat_to_lrat_seconds": convert_seconds,
        "lrat_check_returncode": checked.returncode,
        "lrat_check_seconds": check_seconds,
    }


def gzip_deterministic(path: Path) -> dict[str, object]:
    before = {"sha256": digest(path), "bytes": path.stat().st_size}
    destination = Path(str(path) + ".gz")
    with path.open("rb") as source, destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0) as target:
            shutil.copyfileobj(source, target, 1 << 20)
    path.unlink()
    return {
        **before,
        "gzip_path": destination.name,
        "gzip_sha256": digest(destination),
        "gzip_bytes": destination.stat().st_size,
    }


def invoke_manifest_audit(checker: Path, parent: Path, mapping: Path, manifest: Path, report: Path) -> dict[str, object]:
    run(
        [
            sys.executable,
            str(checker),
            "--parent",
            str(parent),
            "--map",
            str(mapping),
            "--manifest",
            str(manifest),
            "--report",
            str(report),
        ],
        timeout=180,
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    if payload.get("status") != "cube_manifest_audit_pass":
        raise AssertionError("independent cube audit failed")
    return payload


def invoke_normalization_audit(
    normalizer: Path,
    order: int,
    q: int,
    normalized: Path,
    base_cnf: Path,
    mapping: Path,
    summary: Path,
    report: Path,
) -> dict[str, object]:
    run(
        [
            sys.executable,
            str(normalizer),
            "--order",
            str(order),
            "--degree-q",
            str(q),
            "--normalized-cnf",
            str(normalized),
            "--base-cnf",
            str(base_cnf),
            "--map",
            str(mapping),
            "--summary",
            str(summary),
            "--report",
            str(report),
        ],
        timeout=180,
    )
    return json.loads(report.read_text(encoding="utf-8"))


def check_sat_model(
    stdout: str,
    leaf: dict[str, object],
    output: Path,
    checker_b: Path,
) -> dict[str, object]:
    bits = base.parse_model(stdout, 861)
    for literal in leaf["literals"]:
        expected = literal > 0
        if bits[abs(literal) - 1] != expected:
            raise AssertionError("SAT model violates cube")
    independent, cliques = base.violation_scan(42, 5, bits)
    degrees = base.degree_scan(42, bits)
    root_pattern = all(bits[edge_variable(0, vertex) - 1] == (vertex <= 20) for vertex in range(1, 42))
    if independent or cliques or not all(degree in {20, 21} for degree in degrees) or not root_pattern:
        raise AssertionError("SAT model failed Python full scan")
    padded = bits + [False] * ((-len(bits)) % 6)
    graph6 = bytes(
        [42 + 63]
        + [
            63 + sum((1 if padded[offset + index] else 0) << (5 - index) for index in range(6))
            for offset in range(0, len(padded), 6)
        ]
    ) + b"\n"
    model_path = output / f"leaf-{leaf['id']}.model.g6"
    model_path.write_bytes(graph6)
    checked, _ = run([str(checker_b), "--format", "graph6", "--input", str(model_path)], timeout=120)
    payload = json.loads(checked.stdout)["graphs"][0]
    if payload["zero_k5"] or payload["one_k5"] or payload["degrees"] != degrees:
        raise AssertionError("independent C full scan rejected SAT model")
    return {
        "graph6_path": model_path.name,
        "graph6_sha256": digest(model_path),
        "python_five_subset_and_degree_scan": True,
        "c_recursive_bitset_scan": True,
        "cube_literals_checked": True,
        "degree_histogram": {str(value): degrees.count(value) for value in sorted(set(degrees))},
    }


def main() -> int:
    if len(sys.argv) != 13:
        raise SystemExit(
            "usage: run_q20_cube_pilot.py GENERATOR NORMALIZER MANIFEST_CHECKER "
            "Q20_PARENT_GZ Q20_MAP DRAT_C LRAT_C CHECKER_B_C OUTPUT_DIR REPORT "
            "LEAF_SECONDS STORAGE_MIB"
        )
    (
        generator,
        normalizer,
        manifest_checker,
        q20_parent,
        q20_map,
        drat_source,
        lrat_source,
        checker_b_source,
        output_dir,
        report_path,
        leaf_seconds_raw,
        storage_mib_raw,
    ) = sys.argv[1:]
    generator = Path(generator).resolve()
    normalizer = Path(normalizer).resolve()
    manifest_checker = Path(manifest_checker).resolve()
    q20_parent = Path(q20_parent).resolve()
    q20_map = Path(q20_map).resolve()
    drat_source = Path(drat_source).resolve()
    lrat_source = Path(lrat_source).resolve()
    checker_b_source = Path(checker_b_source).resolve()
    output_dir = Path(output_dir).resolve()
    report_path = Path(report_path).resolve()
    leaf_seconds = int(leaf_seconds_raw)
    storage_limit = int(storage_mib_raw) * 1024 * 1024
    if leaf_seconds != 20 or storage_limit != AGGREGATE_STORAGE_LIMIT:
        raise ValueError("pilot contract requires 20 seconds per leaf and 256 MiB retained storage")
    if output_dir.exists() or report_path.exists():
        raise ValueError("output directory or report already exists")
    compiler = shutil.which("gcc") or shutil.which("clang")
    cadical = shutil.which("cadical")
    if compiler is None or cadical is None:
        raise RuntimeError("compiler or CaDiCaL unavailable")
    if digest(q20_parent) != EXPECTED_Q20_GZIP_SHA256 or digest(q20_map) != EXPECTED_Q20_MAP_SHA256:
        raise AssertionError("frozen q20 compressed parent or map hash mismatch")
    _, q20_variables, q20_clauses, _, q20_sha256, _ = read_parent(q20_parent)
    if (
        q20_sha256 != EXPECTED_Q20_SHA256
        or q20_variables != EXPECTED_Q20_VARIABLES
        or q20_clauses != EXPECTED_Q20_CLAUSES
    ):
        raise AssertionError("frozen q20 uncompressed parent mismatch")
    output_dir.mkdir(parents=True)
    toy_dir = output_dir / "toy-r33"
    toy_dir.mkdir()
    production_dir = output_dir / "production"
    production_dir.mkdir()

    with tempfile.TemporaryDirectory(prefix="r55-cube-tools-") as temporary:
        tool_dir = Path(temporary)
        drat, lrat_check, checker_b = compile_tools(
            compiler, drat_source, lrat_source, checker_b_source, tool_dir
        )

        toy_base = toy_dir / "base.cnf"
        toy_base_map = toy_dir / "base.map.tsv"
        toy_base_summary = toy_dir / "base.summary.json"
        toy_parent = toy_dir / "normalized.cnf"
        toy_map = toy_dir / "normalized.map.tsv"
        toy_summary = toy_dir / "normalized.summary.json"
        run(
            [
                sys.executable,
                str(generator),
                "--order",
                "6",
                "--clique-size",
                "3",
                "--degree-q",
                "2",
                "--cnf",
                str(toy_base),
                "--map",
                str(toy_base_map),
                "--summary",
                str(toy_base_summary),
            ]
        )
        run(
            [
                sys.executable,
                str(generator),
                "--order",
                "6",
                "--clique-size",
                "3",
                "--degree-q",
                "2",
                "--fix-root-neighborhood",
                "--cnf",
                str(toy_parent),
                "--map",
                str(toy_map),
                "--summary",
                str(toy_summary),
            ]
        )
        toy_normalization = invoke_normalization_audit(
            normalizer,
            6,
            2,
            toy_parent,
            toy_base,
            toy_map,
            toy_summary,
            toy_dir / "normalization.audit.json",
        )
        if toy_normalization.get("status") != "fixed_root_normalization_audit_pass":
            raise AssertionError("toy normalization audit failed")
        toy_manifest_path = toy_dir / "cube-manifest.json"
        toy_manifest = build_manifest(
            toy_parent,
            toy_map,
            6,
            2,
            [[1, 3], [1, 4], [2, 4], [2, 5]],
            "normalized R(3,3,6) degree-{2,3} control",
            toy_manifest_path,
        )
        toy_audit = invoke_manifest_audit(
            manifest_checker,
            toy_parent,
            toy_map,
            toy_manifest_path,
            toy_dir / "cube-manifest.audit.json",
        )
        toy_results: list[dict[str, object]] = []
        for leaf in toy_manifest["leaves"]:
            leaf_cnf = toy_dir / f"leaf-{leaf['id']}.cnf"
            proof = toy_dir / f"leaf-{leaf['id']}.drat"
            lrat = toy_dir / f"leaf-{leaf['id']}.lrat"
            materialize_leaf(toy_parent, leaf, leaf_cnf)
            solved, solve_seconds = run(
                [cadical, "-q", str(leaf_cnf), str(proof)], accepted=(20,), timeout=60
            )
            certificate = verify_certificate(drat, lrat_check, leaf_cnf, proof, lrat)
            if certificate["target_cnf_sha256"] != leaf["leaf_uncompressed_sha256"]:
                raise AssertionError("toy certificate target binding mismatch")
            toy_results.append(
                {
                    "id": leaf["id"],
                    "returncode": solved.returncode,
                    "solver_seconds": solve_seconds,
                    "certificate": certificate,
                }
            )
        target_binding_mutation_rejected = (
            toy_results[0]["certificate"]["target_cnf_sha256"]
            != toy_manifest["parent"]["uncompressed_sha256"]
        )
        if not target_binding_mutation_rejected:
            raise AssertionError("leaf proof was not bound to its physical target")

        production_manifest_path = production_dir / "cube-manifest.json"
        production_manifest = build_manifest(
            q20_parent,
            q20_map,
            42,
            20,
            [[1, 21], [2, 21], [2, 22], [3, 22]],
            "normalized Ramsey(5,5,42) degree-{20,21} q=20 branch",
            production_manifest_path,
        )
        production_audit = invoke_manifest_audit(
            manifest_checker,
            q20_parent,
            q20_map,
            production_manifest_path,
            production_dir / "cube-manifest.audit.json",
        )
        production_results: list[dict[str, object]] = []
        retained_storage = 0
        stop_reason = "all_16_leaf_budgets_executed"
        for leaf in production_manifest["leaves"]:
            leaf_cnf = production_dir / f"leaf-{leaf['id']}.cnf"
            proof = production_dir / f"leaf-{leaf['id']}.partial-or-final.drat"
            stdout_path = production_dir / f"leaf-{leaf['id']}.stdout"
            stderr_path = production_dir / f"leaf-{leaf['id']}.stderr"
            materialize_leaf(q20_parent, leaf, leaf_cnf)
            started = time.monotonic()
            solved = subprocess.run(
                [cadical, "-q", "-t", str(leaf_seconds), str(leaf_cnf), str(proof)],
                text=True,
                capture_output=True,
                preexec_fn=proof_file_limit,
            )
            solve_seconds = time.monotonic() - started
            stdout_path.write_text(solved.stdout, encoding="ascii")
            stderr_path.write_text(solved.stderr, encoding="ascii")
            result: dict[str, object] = {
                "id": leaf["id"],
                "bits": leaf["bits"],
                "literals": leaf["literals"],
                "leaf_cnf_sha256": digest(leaf_cnf),
                "returncode": solved.returncode,
                "solver_seconds": solve_seconds,
                "command": ["cadical", "-q", "-t", str(leaf_seconds), f"leaf-{leaf['id']}.cnf", f"leaf-{leaf['id']}.partial-or-final.drat"],
            }
            if result["leaf_cnf_sha256"] != leaf["leaf_uncompressed_sha256"]:
                raise AssertionError("production solver target mismatch")
            if solved.returncode == 10:
                result["status"] = "sat_verified"
                result["model"] = check_sat_model(solved.stdout, leaf, production_dir, checker_b)
            elif solved.returncode == 20:
                lrat = production_dir / f"leaf-{leaf['id']}.lrat"
                certificate = verify_certificate(drat, lrat_check, leaf_cnf, proof, lrat)
                if certificate["target_cnf_sha256"] != leaf["leaf_uncompressed_sha256"]:
                    raise AssertionError("production certificate target mismatch")
                result["status"] = "unsat_verified"
                result["certificate"] = certificate
            else:
                result["status"] = "unknown"
                result["qualification"] = "timeout, interruption, or proof limit; no exclusion"
            leaf_cnf.unlink()
            if proof.exists():
                proof_storage = gzip_deterministic(proof)
                retained_storage += int(proof_storage["gzip_bytes"])
                result["proof_storage"] = proof_storage
            lrat_path = production_dir / f"leaf-{leaf['id']}.lrat"
            if lrat_path.exists():
                lrat_storage = gzip_deterministic(lrat_path)
                retained_storage += int(lrat_storage["gzip_bytes"])
                result["lrat_storage"] = lrat_storage
            result["aggregate_retained_certificate_bytes_after_leaf"] = retained_storage
            production_results.append(result)
            (production_dir / f"leaf-{leaf['id']}.result.json").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            if result["status"] == "sat_verified":
                stop_reason = f"verified_sat_leaf_{leaf['id']}"
                break
            if retained_storage > storage_limit:
                stop_reason = f"retained_storage_gate_exceeded_after_{leaf['id']}"
                break

    statuses = {status: sum(row["status"] == status for row in production_results) for status in ("sat_verified", "unsat_verified", "unknown")}
    executed_ids = [row["id"] for row in production_results]
    unexecuted_ids = [leaf["id"] for leaf in production_manifest["leaves"] if leaf["id"] not in executed_ids]
    if statuses["sat_verified"]:
        conclusion = "A production cube yielded a dual-checked q=20 order-42 Ramsey graph."
    elif statuses["unsat_verified"] == 16:
        conclusion = "All 16 independently covered cubes are proof-checked UNSAT, excluding the normalized q=20 branch only."
    elif statuses["unsat_verified"]:
        conclusion = "Some named cubes are proof-checked UNSAT; unresolved cubes prevent any parent-formula exclusion."
    else:
        conclusion = "No production leaf resolved; the 16-cube pilot changes no mathematical bound."
    payload = {
        "schema_version": 1,
        "status": "q20_cube_pilot_complete",
        "source_status": "43 <= R(5,5) <= 46; DS1.18 revision 18 checked 2026-07-21",
        "scope": "fixed-root order-42 degree-{20,21} q=20 branch only",
        "hypothesis": "a complete four-variable cover exposes at least one leaf decidable in 20 seconds with a checkable result",
        "toy_gate": {
            "normalization_audit": toy_normalization,
            "manifest_audit": toy_audit,
            "all_16_unsat_with_checked_drat_and_lrat": len(toy_results) == 16,
            "target_binding_parent_substitution_rejected": target_binding_mutation_rejected,
            "leaf_results": toy_results,
        },
        "production": {
            "parent_uncompressed_sha256": q20_sha256,
            "parent_gzip_sha256": digest(q20_parent),
            "map_sha256": digest(q20_map),
            "manifest_sha256": digest(production_manifest_path),
            "manifest_audit": production_audit,
            "leaf_seconds": leaf_seconds,
            "per_leaf_proof_limit_bytes": PROOF_LIMIT_BYTES,
            "aggregate_storage_limit_bytes": storage_limit,
            "retained_certificate_bytes": retained_storage,
            "status_counts": statuses,
            "executed_leaf_ids": executed_ids,
            "unexecuted_leaf_ids": unexecuted_ids,
            "stop_reason": stop_reason,
            "leaf_results": production_results,
        },
        "orbit_scope": {
            "raw_leaves_retained": 16,
            "path_reversal_orbits": 10,
            "symmetry_quotient_used": False,
            "qualification": "orbit classes are a cost diagnostic only; no proof transport is assumed",
        },
        "conclusion": conclusion,
        "tool_versions": {
            "python": sys.version.split()[0],
            "compiler": subprocess.run([compiler, "--version"], text=True, capture_output=True).stdout.splitlines()[0],
            "cadical": subprocess.run([cadical, "--version"], text=True, capture_output=True).stdout.strip(),
        },
        "independence": {
            "manifest_producer_sha256": digest(Path(__file__)),
            "manifest_checker_sha256": digest(manifest_checker),
            "checker_imports_producer": False,
            "proof_checkers": [digest(drat_source), digest(lrat_source)],
            "sat_model_checkers": "Python direct five-subset scan plus independently compiled C recursive-bitset scan",
        },
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "report": str(report_path),
                "report_sha256": digest(report_path),
                "production_status_counts": statuses,
                "stop_reason": stop_reason,
                "conclusion": conclusion,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
