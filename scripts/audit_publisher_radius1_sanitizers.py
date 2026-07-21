#!/usr/bin/env python3
"""Rebuild Checker B with UBSan and compare its full ledger to the report.

AddressSanitizer is intentionally excluded because the required experiment
harness enforces RLIMIT_AS (at most 32 GiB), while ASan reserves a much larger
virtual shadow mapping before running the checker.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit_publisher_radius1_sanitizers.py CHECKER_B_C BODY REPORT")
    source = Path(sys.argv[1]).resolve()
    body = Path(sys.argv[2]).resolve()
    report_path = Path(sys.argv[3]).resolve()
    compiler = shutil.which("gcc")
    if compiler is None:
        raise RuntimeError("gcc not found")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="r55-radius1-sanitizer-") as temporary:
        binary = Path(temporary) / "checker_b_sanitized"
        command = [
            compiler,
            "-std=c11",
            "-O1",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=undefined",
            "-fno-omit-frame-pointer",
            str(source),
            "-o",
            str(binary),
        ]
        subprocess.run(command, check=True)
        environment = os.environ.copy()
        environment["UBSAN_OPTIONS"] = "halt_on_error=1"
        result = subprocess.run(
            [str(binary), "--input", str(body)],
            check=True,
            capture_output=True,
            env=environment,
        )
        if result.stderr:
            raise RuntimeError(f"sanitizer diagnostic: {result.stderr.decode('utf-8', 'replace')}")
        checked = json.loads(result.stdout)
        if checked["seed"]["zero_k5"] != report["seed"]["zero_k5"]:
            raise AssertionError("sanitized seed zero-K5 identities disagree")
        if checked["seed"]["one_k5"] != report["seed"]["one_k5"]:
            raise AssertionError("sanitized seed one-K5 identities disagree")
        if len(checked["radius1"]) != len(report["complete_flip_ledger"]):
            raise AssertionError("sanitized ledger length disagrees")
        for expected, observed in zip(report["complete_flip_ledger"], checked["radius1"], strict=True):
            expected = dict(expected)
            expected.pop("total_burden")
            if expected != observed:
                raise AssertionError(f"sanitized ledger identity mismatch at {observed['edge']}")
        print(json.dumps({
            "status": "sanitized_full_ledger_pass",
            "checked_flips": len(checked["radius1"]),
            "checker_source_sha256": digest_bytes(source.read_bytes()),
            "body_sha256": digest_bytes(body.read_bytes()),
            "report_sha256": digest_bytes(report_path.read_bytes()),
            "sanitized_binary_sha256": digest_bytes(binary.read_bytes()),
            "sanitized_output_sha256": digest_bytes(result.stdout),
            "compile_command": command[:-1] + ["<temporary>/checker_b_sanitized"],
            "compiler_version": subprocess.run(
                [compiler, "--version"], check=True, capture_output=True, text=True
            ).stdout.splitlines()[0],
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
