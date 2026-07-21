#!/usr/bin/env python3
"""Cold audit of the retained normalized q=20 UNKNOWN packet."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


MAIN_REPORT_SHA256 = "c0ee1711e81b6db391bf68a517662e55bd7a92dab3cdd2fab6f6e090a46c5a01"
EXPECTED_RAMSEY_LEDGER = "c3ed87c4609c629948e6b51715f65fea99efed79af5baacbc96805041e9d1945"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def decompress(source: Path, destination: Path) -> dict[str, object]:
    hasher = hashlib.sha256()
    size = 0
    with gzip.open(source, "rb") as input_stream, destination.open("wb") as output_stream:
        for block in iter(lambda: input_stream.read(1 << 20), b""):
            hasher.update(block)
            size += len(block)
            output_stream.write(block)
    return {"sha256": hasher.hexdigest(), "bytes": size}


def main() -> int:
    if len(sys.argv) != 9:
        raise SystemExit(
            "usage: audit_almost_regular_42_q20_normalized.py MAIN_REPORT PACKET BASE_CNF_GZ "
            "NORMALIZER LEDGER_B_C DRAT_C AUDIT_REPORT REPLAY_NORMALIZATION_REPORT"
        )
    (
        main_report,
        packet,
        base_cnf_gz,
        normalizer,
        ledger_source,
        drat_source,
        audit_report,
        replay_normalization_report,
    ) = map(lambda value: Path(value).resolve(), sys.argv[1:])
    if audit_report.exists() or replay_normalization_report.exists():
        raise ValueError("audit output already exists")
    if digest(main_report) != MAIN_REPORT_SHA256:
        raise ValueError("main report hash lock failed")
    report = json.loads(main_report.read_text(encoding="utf-8"))
    production = report["production"]
    if (
        production["result"]["status"] != "unknown"
        or production["solver"]["returncode"] != 0
        or production["generator_summary"]["clauses"] != 1844093
    ):
        raise AssertionError("main report is not the declared normalized UNKNOWN pilot")
    cnf_gz = packet / production["cnf_storage"]["gzip_path"]
    proof_gz = packet / production["proof_storage"]["gzip_path"]
    if (
        digest(cnf_gz) != production["cnf_storage"]["gzip_sha256"]
        or digest(proof_gz) != production["proof_storage"]["gzip_sha256"]
    ):
        raise AssertionError("compressed artifact hash mismatch")
    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise RuntimeError("compiler unavailable")

    with tempfile.TemporaryDirectory(prefix="r55-q20-normalized-cold-") as temporary:
        root = Path(temporary)
        cnf = root / "q20-normalized.cnf"
        proof = root / "q20-normalized.partial.drat"
        cnf_result = decompress(cnf_gz, cnf)
        proof_result = decompress(proof_gz, proof)
        if cnf_result != {
            "sha256": production["cnf_storage"]["sha256"],
            "bytes": production["cnf_storage"]["bytes"],
        }:
            raise AssertionError("uncompressed CNF manifest mismatch")
        if proof_result != {
            "sha256": production["proof_storage"]["sha256"],
            "bytes": production["proof_storage"]["bytes"],
        }:
            raise AssertionError("uncompressed proof manifest mismatch")

        subprocess.run(
            [
                sys.executable,
                str(normalizer),
                "--order",
                "42",
                "--degree-q",
                "20",
                "--normalized-cnf",
                str(cnf_gz),
                "--base-cnf",
                str(base_cnf_gz),
                "--map",
                str(packet / "q20-normalized.map.tsv"),
                "--summary",
                str(packet / "q20-normalized.generator.json"),
                "--report",
                str(replay_normalization_report),
            ],
            check=True,
            text=True,
            capture_output=True,
            timeout=300,
        )
        replay = json.loads(replay_normalization_report.read_text(encoding="utf-8"))
        retained_normalization = json.loads(
            (packet / "q20-normalized.audit-a.json").read_text(encoding="utf-8")
        )
        if replay != retained_normalization:
            raise AssertionError("cold normalization replay differs from retained audit")

        ledger_b = root / "ledger-b"
        ledger = root / "ramsey-ledger.txt"
        subprocess.run(
            [
                compiler,
                "-std=c11",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(ledger_source),
                "-o",
                str(ledger_b),
            ],
            check=True,
        )
        subprocess.run(
            [str(ledger_b), "42", "5", str(ledger)], check=True, capture_output=True
        )
        if digest(ledger) != EXPECTED_RAMSEY_LEDGER:
            raise AssertionError("cold C Ramsey-ledger mismatch")

        drat_trim = root / "drat-trim"
        subprocess.run(
            [compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat_trim)],
            check=True,
        )
        checked = subprocess.run(
            [str(drat_trim), str(cnf), str(proof)],
            text=True,
            capture_output=True,
            timeout=300,
        )
        if checked.returncode == 0 or "s VERIFIED" in checked.stdout:
            raise AssertionError("timeout stream unexpectedly verifies as a refutation")

    payload = {
        "schema_version": 1,
        "status": "almost_regular_42_q20_normalized_cold_audit_pass",
        "main_report_sha256": MAIN_REPORT_SHA256,
        "cnf": {
            **cnf_result,
            "clauses": 1844093,
            "variables": 71421,
            "exactly_base_plus_41_units": True,
            "cold_normalization_audit_sha256": digest(replay_normalization_report),
        },
        "partial_proof": {
            **proof_result,
            "drat_trim_returncode": checked.returncode,
            "verified": False,
            "qualification": "expected non-certificate from a solver timeout",
        },
        "independent_c_nested_loop_ramsey_ledger": True,
        "normalization_mutation_replay": replay["mutation_rejections"],
        "scope": "artifact integrity, normalization, and bounded-cost audit only; no SAT or UNSAT claim",
    }
    audit_report.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "audit_report": str(audit_report),
                "audit_report_sha256": digest(audit_report),
                "partial_proof_verified": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
