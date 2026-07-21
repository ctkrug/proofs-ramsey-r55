#!/usr/bin/env python3
"""Bounded one-orbit pilot for the raw-origin burden-one encodings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import run_two_orbit_burden_one_gate as gate


def timed(command: list[str], *, accepted=(0,), timeout=120):
    started = time.monotonic()
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    elapsed = time.monotonic() - started
    if result.returncode not in accepted:
        raise RuntimeError(f"command failed: {command}\n{result.stdout}\n{result.stderr}")
    return result, elapsed


def main() -> int:
    if len(sys.argv) != 7:
        raise SystemExit(
            "usage: run_two_orbit_burden_one_pilot.py GENERATOR_A GENERATOR_B_C BODY1 BODY2 DRAT_TRIM_C REPORT"
        )
    generator_a = Path(sys.argv[1]).resolve()
    generator_b_source = Path(sys.argv[2]).resolve()
    body1 = Path(sys.argv[3]).resolve()
    body2 = Path(sys.argv[4]).resolve()
    drat_source = Path(sys.argv[5]).resolve()
    report = Path(sys.argv[6]).resolve()
    if report.exists():
        raise ValueError("pilot report already exists")
    if gate.digest(body1) != gate.SOURCE_SHA256 or body1.read_bytes() != body2.read_bytes():
        raise ValueError("publisher source hash/identity gate failed")
    compiler = shutil.which("gcc") or shutil.which("clang")
    cadical = shutil.which("cadical")
    if compiler is None or cadical is None:
        raise RuntimeError("compiler or CaDiCaL unavailable")
    with tempfile.TemporaryDirectory(prefix="r55-burden-one-pilot-") as temporary:
        root = Path(temporary)
        generator_b = root / "generator-b"
        drat_trim = root / "drat-trim"
        timed([compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(generator_b_source), "-o", str(generator_b)])
        timed([compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat_trim)])
        a = [root / name for name in ("a.cnf", "a.tsv", "a.map", "a.json")]
        b = [root / name for name in ("b.cnf", "b.tsv", "b.map", "b.json")]
        timed([sys.executable, str(generator_a), str(body1), "0", *map(str, a)])
        timed([str(generator_b), str(body1), "0", *map(str, b)])
        if a[1].read_bytes() != b[1].read_bytes() or a[2].read_bytes() != b[2].read_bytes():
            raise AssertionError("pilot raw ledgers or origin maps differ")
        summary_a = json.loads(a[3].read_text(encoding="ascii"))
        summary_b = json.loads(b[3].read_text(encoding="ascii"))
        if summary_a["raw_active_origins"] != 215 or summary_b["raw_active_origins"] != 215:
            raise AssertionError("pilot did not reproduce 215 raw origins")
        gate.exact_formula_audit(a[0], a[1], 43, prefix=True)
        gate.exact_formula_audit(b[0], b[1], 43, prefix=False)
        results = {}
        for label, cnf in (("python_prefix", a[0]), ("c_suffix", b[0])):
            proof = root / f"{label}.drat"
            result = gate.solve_and_check(cadical, drat_trim, cnf, proof, timeout=120)
            result.pop("solver_stdout")
            result.pop("solver_stderr")
            if result["status"] != "unsat":
                raise AssertionError("distance-6 burden-one pilot was not UNSAT")
            results[label] = result
        payload = {
            "schema_version": 1,
            "status": "two_orbit_burden_one_pilot_pass",
            "scope": "distance-6-only slice, raw monochromatic-K5 burden at most one",
            "source_sha256": gate.SOURCE_SHA256,
            "raw_active_origins": 215,
            "raw_ledger_sha256": gate.digest(a[1]),
            "origin_mapping_sha256": gate.digest(a[2]),
            "raw_ledger_byte_identity": True,
            "origin_mapping_byte_identity": True,
            "exact_formula_audits": True,
            "results": results,
            "generator_hashes": {
                "python": gate.digest(generator_a),
                "c_source": gate.digest(generator_b_source),
                "c_binary": gate.digest(generator_b),
            },
            "proof_checker": {
                "source_sha256": gate.digest(drat_source),
                "binary_sha256": gate.digest(drat_trim),
            },
            "conclusion": "Both independent raw-origin encodings prove the known distance-6 slice has no assignment of burden at most one.",
        }
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": payload["status"],
            "report": str(report),
            "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
            "raw_active_origins": 215,
            "proofs_verified": len(results),
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
