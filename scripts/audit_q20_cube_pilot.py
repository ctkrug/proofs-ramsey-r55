#!/usr/bin/env python3
"""Cold audit of the retained q=20 16-cube pilot packet."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import BinaryIO


MAIN_REPORT_SHA256 = "864f2c67df3e963ba358e1c430880b1f2f39e89508830aca9fdfb06faa427251"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def open_binary(path: Path) -> BinaryIO:
    return gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")


def run(command: list[str], timeout: int = 300) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.monotonic()
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    return result, time.monotonic() - started


def materialize(parent: Path, leaf: dict[str, object], destination: Path) -> None:
    with open_binary(parent) as source, destination.open("wb") as target:
        fields = source.readline().decode("ascii").split()
        variables, clauses = map(int, fields[2:])
        target.write(f"p cnf {variables} {clauses + 4}\n".encode("ascii"))
        shutil.copyfileobj(source, target, 1 << 20)
        for literal in leaf["literals"]:
            target.write(f"{literal} 0\n".encode("ascii"))


def main() -> int:
    if len(sys.argv) != 11:
        raise SystemExit(
            "usage: audit_q20_cube_pilot.py MAIN_REPORT PACKET PARENT MAP "
            "MANIFEST_CHECKER DRAT_C LRAT_C AUDIT_REPORT REPLAY_MANIFEST_AUDIT EXPERIMENT_JSON"
        )
    (
        main_report,
        packet,
        parent,
        mapping,
        manifest_checker,
        drat_source,
        lrat_source,
        audit_report,
        replay_manifest_audit,
        experiment_json,
    ) = map(lambda value: Path(value).resolve(), sys.argv[1:])
    if audit_report.exists() or replay_manifest_audit.exists():
        raise ValueError("cold-audit output already exists")
    if digest(main_report) != MAIN_REPORT_SHA256:
        raise AssertionError("main report hash lock failed")
    report = json.loads(main_report.read_text(encoding="utf-8"))
    if report["production"]["status_counts"] != {
        "sat_verified": 0,
        "unknown": 16,
        "unsat_verified": 0,
    }:
        raise AssertionError("unexpected production disposition")
    experiment = json.loads(experiment_json.read_text(encoding="utf-8"))
    if experiment.get("returncode") != 0 or experiment.get("timed_out"):
        raise AssertionError("experiment wrapper did not complete cleanly")

    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise RuntimeError("compiler unavailable")
    packet_manifest = packet / "production" / "cube-manifest.json"
    manifest = json.loads(packet_manifest.read_text(encoding="utf-8"))
    checked = subprocess.run(
        [
            sys.executable,
            str(manifest_checker),
            "--parent",
            str(parent),
            "--map",
            str(mapping),
            "--manifest",
            str(packet_manifest),
            "--report",
            str(replay_manifest_audit),
        ],
        text=True,
        capture_output=True,
        timeout=300,
    )
    if checked.returncode != 0:
        raise RuntimeError(f"manifest replay failed: {checked.stdout}\n{checked.stderr}")
    replay = json.loads(replay_manifest_audit.read_text(encoding="utf-8"))
    if replay.get("status") != "cube_manifest_audit_pass":
        raise AssertionError("manifest replay status mismatch")

    with tempfile.TemporaryDirectory(prefix="r55-cube-cold-") as temporary:
        root = Path(temporary)
        drat = root / "drat-trim"
        lrat_check = root / "lrat-check"
        for command in (
            [compiler, "-std=c99", "-O2", str(drat_source), "-o", str(drat)],
            [compiler, "-std=c99", "-DLONGTYPE", "-O2", str(lrat_source), "-o", str(lrat_check)],
        ):
            compiled, _ = run(command)
            if compiled.returncode != 0:
                raise RuntimeError(f"checker compilation failed: {compiled.stderr}")

        toy_results: list[dict[str, object]] = []
        for word in [f"{value:04b}" for value in range(16)]:
            cnf = packet / "toy-r33" / f"leaf-{word}.cnf"
            proof = packet / "toy-r33" / f"leaf-{word}.drat"
            retained_lrat = packet / "toy-r33" / f"leaf-{word}.lrat"
            regenerated_lrat = root / f"toy-{word}.lrat"
            converted, convert_seconds = run(
                [str(drat), str(cnf), str(proof), "-L", str(regenerated_lrat)]
            )
            checked_lrat, check_seconds = run([str(lrat_check), str(cnf), str(regenerated_lrat)])
            checked_retained, retained_seconds = run([str(lrat_check), str(cnf), str(retained_lrat)])
            if any(result.returncode != 0 for result in (converted, checked_lrat, checked_retained)):
                raise AssertionError(f"toy certificate replay failed for {word}")
            toy_results.append(
                {
                    "id": word,
                    "cnf_sha256": digest(cnf),
                    "drat_sha256": digest(proof),
                    "retained_lrat_sha256": digest(retained_lrat),
                    "regenerated_lrat_sha256": digest(regenerated_lrat),
                    "drat_to_lrat_seconds": convert_seconds,
                    "regenerated_lrat_check_seconds": check_seconds,
                    "retained_lrat_check_seconds": retained_seconds,
                }
            )

        production_results: list[dict[str, object]] = []
        report_rows = {row["id"]: row for row in report["production"]["leaf_results"]}
        for leaf in manifest["leaves"]:
            word = leaf["id"]
            leaf_cnf = root / f"production-{word}.cnf"
            materialize(parent, leaf, leaf_cnf)
            if digest(leaf_cnf) != leaf["leaf_uncompressed_sha256"]:
                raise AssertionError(f"cold leaf reconstruction mismatch for {word}")
            proof_gz = packet / "production" / report_rows[word]["proof_storage"]["gzip_path"]
            storage = report_rows[word]["proof_storage"]
            if digest(proof_gz) != storage["gzip_sha256"] or proof_gz.stat().st_size != storage["gzip_bytes"]:
                raise AssertionError(f"compressed proof identity mismatch for {word}")
            proof = root / f"production-{word}.drat"
            proof_hash = hashlib.sha256()
            proof_bytes = 0
            with gzip.open(proof_gz, "rb") as source, proof.open("wb") as target:
                for block in iter(lambda: source.read(1 << 20), b""):
                    proof_hash.update(block)
                    proof_bytes += len(block)
                    target.write(block)
            if proof_hash.hexdigest() != storage["sha256"] or proof_bytes != storage["bytes"]:
                raise AssertionError(f"uncompressed proof identity mismatch for {word}")
            verified, seconds = run([str(drat), str(leaf_cnf), str(proof)], timeout=300)
            if verified.returncode == 0:
                raise AssertionError(f"UNKNOWN leaf {word} unexpectedly has a valid complete DRAT proof")
            production_results.append(
                {
                    "id": word,
                    "leaf_cnf_sha256": digest(leaf_cnf),
                    "partial_drat_sha256": proof_hash.hexdigest(),
                    "partial_drat_bytes": proof_bytes,
                    "fresh_drat_trim_returncode": verified.returncode,
                    "fresh_drat_trim_seconds": seconds,
                    "certificate_valid": False,
                }
            )
            leaf_cnf.unlink()
            proof.unlink()

    payload = {
        "status": "q20_cube_pilot_cold_audit_pass",
        "main_report_sha256": digest(main_report),
        "experiment_json_sha256": digest(experiment_json),
        "manifest_sha256": digest(packet_manifest),
        "manifest_replay_sha256": digest(replay_manifest_audit),
        "toy_certificates_replayed": len(toy_results),
        "toy_all_drat_to_lrat_and_lrat_checks_pass": len(toy_results) == 16,
        "toy_results": toy_results,
        "production_leaves_reconstructed": len(production_results),
        "production_all_partial_proofs_rejected": all(
            not row["certificate_valid"] for row in production_results
        ),
        "production_results": production_results,
        "scope": "cold replay of retained 16-cube packet; no SAT/UNSAT result for production leaves",
    }
    audit_report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "report": str(audit_report),
                "report_sha256": digest(audit_report),
                "toy_certificates_replayed": len(toy_results),
                "production_partial_proofs_rejected": len(production_results),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
