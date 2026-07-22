#!/usr/bin/env python3
"""Build a complete operator receipt for the v3 census validation job."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_JOB = "lab-ramsey-r55-868014a68d6e"
CHECKER = "checkers/validate_known_class_embedding_census.py"
MANIFEST = "artifacts/known-class-embedding-census-v3/output/manifest.jsonl"
CHECKPOINT = "artifacts/known-class-embedding-census-v3/checkpoint.json"
PROGRESS = "artifacts/known-class-embedding-census-v3/progress.json"
RESULT = "artifacts/known-class-embedding-census-v3/validation.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def relative(workspace: Path, path: Path) -> str:
    return path.resolve().relative_to(workspace).as_posix()


def build(workspace: Path, source_state_path: Path, validation_state_path: Path) -> dict[str, object]:
    workspace = workspace.resolve()
    source = load(source_state_path)
    validation = load(validation_state_path)
    if source.get("id") != SOURCE_JOB or (source.get("status") or source.get("event")) != "completed_awaiting_review":
        raise ValueError("source job is not the completed v3 census")
    progress = source.get("latest_progress") or source.get("progress")
    if not isinstance(progress, dict) or progress.get("complete") is not True:
        raise ValueError("source job lacks complete final progress")
    validation_id = str(validation.get("id") or "")
    if (
        not validation_id or validation_id == SOURCE_JOB
        or (validation.get("status") or validation.get("event")) != "completed_awaiting_review"
    ):
        raise ValueError("validation job is not distinct and complete")
    command = validation.get("command")
    expected_command = ["python3", CHECKER, MANIFEST, "--output", RESULT]
    if command != expected_command:
        raise ValueError("validation command mismatch")
    segments = validation.get("segments") or ([validation] if validation.get("runner_result") else [])
    if not isinstance(segments, list) or not segments:
        raise ValueError("validation job has no segment")
    last = segments[-1]
    if not isinstance(last, dict) or last.get("returncode") != 0 or last.get("threshold_failures"):
        raise ValueError("validation segment did not pass")
    runner = json.loads(str(last.get("runner_result") or "{}"))
    experiment_dir = Path(str(runner.get("experiment_dir") or "")).resolve()
    try:
        experiment_dir.relative_to(workspace)
    except ValueError:
        experiment_dir = workspace / str(last.get("output_root") or "") / str(runner.get("id") or "")
    experiment = experiment_dir / "experiment.json"
    stdout = experiment_dir / "stdout.txt"
    experiment_relative = relative(workspace, experiment)
    checker = workspace / CHECKER
    result = workspace / RESULT
    manifest = workspace / MANIFEST
    checked = {
        MANIFEST: sha(manifest),
        CHECKPOINT: sha(workspace / CHECKPOINT),
        PROGRESS: sha(workspace / PROGRESS),
        RESULT: sha(result),
    }
    rows = manifest.read_text(encoding="utf-8").splitlines()
    if len(rows) != 656:
        raise ValueError("final manifest does not contain 656 rows")
    for raw in rows:
        row = json.loads(raw)
        artifact_relative = f"artifacts/known-class-embedding-census-v3/output/{row['artifact']}"
        artifact = workspace / artifact_relative
        actual = sha(artifact)
        if actual != row.get("artifact_sha256"):
            raise ValueError(f"manifest artifact hash mismatch: {artifact_relative}")
        checked[artifact_relative] = actual
    progress_hash = sha(workspace / PROGRESS)
    if progress.get("sha256") != progress_hash:
        raise ValueError("source progress hash mismatch")
    return {
        "schema_version": 1,
        "job_id": SOURCE_JOB,
        "segment": int(source["segment"]),
        "progress_sha256": progress_hash,
        "result": "passed",
        "validator": "standalone full-corpus integrity validator in a distinct lab job",
        "checker_path": CHECKER,
        "checker_sha256": sha(checker),
        "checker_command": expected_command,
        "checker_exit_code": 0,
        "validation_job_id": validation_id,
        "checker_stdout_sha256": sha(stdout),
        "checker_result_path": RESULT,
        "checker_result_sha256": sha(result),
        "execution_record_path": experiment_relative,
        "execution_record_sha256": sha(experiment),
        "checked_artifacts": checked,
        "independence_basis": "Standalone parser rehashes the complete manifest and all 656 gzip artifacts, enforces canonical coverage and mixed gates, and cross-checks stored bitset and NetworkX summaries. It does not independently re-enumerate embeddings; that stronger check is reserved for the cold residual audit.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_state", type=Path)
    parser.add_argument("validation_state", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    workspace = Path.cwd().resolve()
    output = args.output.resolve()
    output.relative_to(workspace)
    if output.exists():
        raise ValueError("validation receipt output already exists")
    receipt = build(workspace, args.source_state, args.validation_state)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(json.dumps({"status": "complete", "checked_artifacts": len(receipt["checked_artifacts"]), "output_sha256": sha(output)}, sort_keys=True))


if __name__ == "__main__":
    main()
