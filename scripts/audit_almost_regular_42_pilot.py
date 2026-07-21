#!/usr/bin/env python3
"""Cold audit of the retained, inconclusive almost-regular q=20 pilot."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


MAIN_REPORT_SHA256 = "1c93796ebf27f29d428194d5910ecb2e59e72598d506dc365021ddbdf7ad53fe"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def decompress_and_audit_cnf(source: Path, destination: Path, production: dict[str, object]) -> dict[str, object]:
    summary = production["generator_summary"]
    storage = production["cnf_storage"]
    whole = hashlib.sha256()
    ramsey = hashlib.sha256()
    size = 0
    clauses = 0
    ramsey_count = 2 * math.comb(42, 5)
    with gzip.open(source, "rb") as input_stream, destination.open("wb") as output_stream:
        header = input_stream.readline()
        expected_header = f"p cnf {summary['variables']} {summary['clauses']}\n".encode("ascii")
        if header != expected_header:
            raise AssertionError("compressed CNF header mismatch")
        whole.update(header)
        size += len(header)
        output_stream.write(header)
        for line in input_stream:
            clauses += 1
            if not line.endswith(b" 0\n"):
                raise AssertionError(f"malformed retained clause {clauses}")
            if clauses <= ramsey_count:
                ramsey.update(line)
            whole.update(line)
            size += len(line)
            output_stream.write(line)
    expected_counter_variables = 42 * 2 * 40 * 21
    at_most_clauses = 2 * 21 * 41 - 3 * 21 + 41 - 1
    expected_degree_clauses = 42 * 2 * at_most_clauses
    if (
        summary["primary_variables"] != 861
        or summary["variables"] != 861 + expected_counter_variables
        or summary["ramsey_clauses"] != ramsey_count
        or summary["degree_clauses"] != expected_degree_clauses
        or clauses != ramsey_count + expected_degree_clauses
        or whole.hexdigest() != storage["sha256"]
        or size != storage["bytes"]
        or ramsey.hexdigest() != summary["ramsey_ledger_sha256"]
    ):
        raise AssertionError("independent production count/hash audit failed")
    return {
        "uncompressed_sha256": whole.hexdigest(),
        "uncompressed_bytes": size,
        "clauses": clauses,
        "ramsey_prefix_sha256": ramsey.hexdigest(),
        "independent_count_formulas": True,
    }


def decompress_hash(source: Path, destination: Path) -> dict[str, object]:
    hasher = hashlib.sha256()
    size = 0
    with gzip.open(source, "rb") as input_stream, destination.open("wb") as output_stream:
        for block in iter(lambda: input_stream.read(1 << 20), b""):
            hasher.update(block)
            size += len(block)
            output_stream.write(block)
    return {"sha256": hasher.hexdigest(), "bytes": size}


def main() -> int:
    if len(sys.argv) != 6:
        raise SystemExit("usage: audit_almost_regular_42_pilot.py MAIN_REPORT PACKET LEDGER_B_C DRAT_TRIM_C AUDIT_REPORT")
    main_report, packet, ledger_source, drat_source, audit_report = map(lambda value: Path(value).resolve(), sys.argv[1:])
    if audit_report.exists():
        raise ValueError("audit report already exists")
    if digest(main_report) != MAIN_REPORT_SHA256:
        raise ValueError("main report hash lock failed")
    report = json.loads(main_report.read_text(encoding="utf-8"))
    production = report["production"]
    if production["result"]["status"] != "unknown" or production["solver"]["returncode"] != 0:
        raise AssertionError("main report is not the declared inconclusive pilot")
    cnf_gz = packet / production["cnf_storage"]["gzip_path"]
    proof_gz = packet / production["proof_storage"]["gzip_path"]
    if digest(cnf_gz) != production["cnf_storage"]["gzip_sha256"] or digest(proof_gz) != production["proof_storage"]["gzip_sha256"]:
        raise AssertionError("compressed artifact hash mismatch")
    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise RuntimeError("compiler unavailable")

    with tempfile.TemporaryDirectory(prefix="r55-almost-regular-audit-") as temporary:
        root = Path(temporary)
        cnf = root / "q20.cnf"
        proof = root / "q20.partial.drat"
        cnf_result = decompress_and_audit_cnf(cnf_gz, cnf, production)
        proof_result = decompress_hash(proof_gz, proof)
        if proof_result != {
            "sha256": production["proof_storage"]["sha256"],
            "bytes": production["proof_storage"]["bytes"],
        }:
            raise AssertionError("partial proof uncompressed manifest mismatch")

        ledger_b = root / "ledger-b"
        ledger = root / "ramsey-ledger.txt"
        subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(ledger_source), "-o", str(ledger_b)],
            check=True,
        )
        subprocess.run([str(ledger_b), "42", "5", str(ledger)], check=True, capture_output=True)
        if digest(ledger) != production["generator_summary"]["ramsey_ledger_sha256"]:
            raise AssertionError("cold C Ramsey-ledger mismatch")

        drat_trim = root / "drat-trim"
        subprocess.run([compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat_trim)], check=True)
        checked = subprocess.run([str(drat_trim), str(cnf), str(proof)], text=True, capture_output=True, timeout=300)
        if checked.returncode == 0 or "s VERIFIED" in checked.stdout:
            raise AssertionError("the solver-timeout stream unexpectedly verifies as a refutation")

    payload = {
        "schema_version": 1,
        "status": "almost_regular_42_q20_cold_audit_pass",
        "main_report_sha256": MAIN_REPORT_SHA256,
        "cnf": cnf_result,
        "partial_proof": {
            **proof_result,
            "drat_trim_returncode": checked.returncode,
            "verified": False,
            "qualification": "expected non-certificate from a solver timeout",
        },
        "independent_c_nested_loop_ramsey_ledger": True,
        "scope": "artifact integrity and encoding/cost audit only; no SAT or UNSAT claim",
    }
    audit_report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "audit_report": str(audit_report),
        "audit_report_sha256": digest(audit_report),
        "clauses": cnf_result["clauses"],
        "partial_proof_verified": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
