from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PREFIX_MANIFEST = ROOT / "artifacts/known-class-embedding-census-v2/output/manifest.jsonl"
PREFIX_CHECKPOINT = ROOT / "artifacts/known-class-embedding-census-v2/checkpoint.json"
CAP60_WRAPPER = ROOT / "scripts/run_known_class_embedding_census_cap60_locked.sh"


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prefix_audit = load(
    "known_class_embedding_resume_prefix_audit",
    "checkers/known_class_embedding_resume_prefix_audit.py",
)
validator = load(
    "validate_known_class_embedding_census",
    "checkers/validate_known_class_embedding_census.py",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_complete_fixture(root: Path) -> tuple[Path, str]:
    output = root / "output"
    hosts = output / "hosts"
    hosts.mkdir(parents=True)
    rows: list[dict[str, object]] = []
    empty_hash = hashlib.sha256(b"").hexdigest()
    for index in range(656):
        case = (
            f"source_record_{index + 1}"
            if index < 328
            else f"complement_record_{index - 327}"
        )
        gate = 30.0 if index < 254 else 60.0
        artifact = hosts / f"{index:03d}-{case}.json.gz"
        summary = {
            "embedding_count": 0,
            "mapping_stream_sha256": empty_hash,
            "vector_occurrences": 0,
            "unique_vector_count": 0,
            "vector_stream_sha256": empty_hash,
        }
        with gzip.open(artifact, "wt", encoding="utf-8") as handle:
            json.dump(
                {
                    "bitset": {"case": case, "unique_vectors": [], **summary},
                    "networkx_summary": summary,
                },
                handle,
                sort_keys=True,
            )
        rows.append(
            {
                "host_index": index,
                "case": case,
                **summary,
                "artifact": artifact.relative_to(output).as_posix(),
                "artifact_sha256": sha(artifact),
                "bitset_seconds": 1.0,
                "networkx_seconds": 2.0,
                "host_seconds": 3.1,
                "host_gate_seconds": gate,
            }
        )
    lines = [json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows]
    manifest = output / "manifest.jsonl"
    manifest.write_text("".join(lines), encoding="utf-8")
    prefix_hash = hashlib.sha256("".join(lines[:254]).encode("utf-8")).hexdigest()
    return manifest, prefix_hash


class ResumePrefixAuditTests(unittest.TestCase):
    def copy_prefix(self, root: Path) -> tuple[Path, Path]:
        copied_output = root / "copied" / "output"
        shutil.copytree(PREFIX_MANIFEST.parent, copied_output)
        copied_checkpoint = root / "copied" / "checkpoint.json"
        shutil.copy2(PREFIX_CHECKPOINT, copied_checkpoint)
        return copied_output / "manifest.jsonl", copied_checkpoint

    def test_exact_prefix_copy_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            copied_manifest, copied_checkpoint = self.copy_prefix(Path(temporary_name))
            report = prefix_audit.audit(
                PREFIX_MANIFEST,
                PREFIX_CHECKPOINT,
                copied_manifest,
                copied_checkpoint,
            )
            self.assertEqual(report["prefix_hosts"], 254)
            self.assertEqual(
                report["original_manifest_sha256"],
                prefix_audit.ORIGINAL_MANIFEST_SHA256,
            )

    def test_reformatted_prefix_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            copied_manifest, copied_checkpoint = self.copy_prefix(Path(temporary_name))
            rows = [json.loads(line) for line in copied_manifest.read_text().splitlines()]
            copied_manifest.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            with self.assertRaisesRegex(AssertionError, "differs"):
                prefix_audit.audit(
                    PREFIX_MANIFEST,
                    PREFIX_CHECKPOINT,
                    copied_manifest,
                    copied_checkpoint,
                )

    def test_mutated_copied_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            copied_manifest, copied_checkpoint = self.copy_prefix(Path(temporary_name))
            first = json.loads(copied_manifest.read_text().splitlines()[0])
            artifact = copied_manifest.parent / first["artifact"]
            artifact.write_bytes(artifact.read_bytes() + b"mutation")
            with self.assertRaisesRegex(AssertionError, "artifact hash mismatch"):
                prefix_audit.audit(
                    PREFIX_MANIFEST,
                    PREFIX_CHECKPOINT,
                    copied_manifest,
                    copied_checkpoint,
                )

    def test_mutated_checkpoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            copied_manifest, copied_checkpoint = self.copy_prefix(Path(temporary_name))
            checkpoint = json.loads(copied_checkpoint.read_text())
            checkpoint["next_host"] = 253
            copied_checkpoint.write_text(json.dumps(checkpoint), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "checkpoint differs"):
                prefix_audit.audit(
                    PREFIX_MANIFEST,
                    PREFIX_CHECKPOINT,
                    copied_manifest,
                    copied_checkpoint,
                )


class FinalValidatorTests(unittest.TestCase):
    def test_mixed_gate_schedule_and_prefix_binding_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            manifest, prefix_hash = build_complete_fixture(Path(temporary_name))
            report = validator.validate(manifest, expected_prefix_sha256=prefix_hash)
            self.assertEqual(report["hosts"], 656)
            self.assertEqual(
                report["aggregate_host_gate_schedule"],
                [
                    {"first_host": 0, "last_host": 253, "seconds": 30.0},
                    {"first_host": 254, "last_host": 655, "seconds": 60.0},
                ],
            )

    def test_wrong_continuation_gate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            manifest, prefix_hash = build_complete_fixture(Path(temporary_name))
            lines = manifest.read_text().splitlines()
            row = json.loads(lines[254])
            row["host_gate_seconds"] = 30.0
            lines[254] = json.dumps(row, sort_keys=True, separators=(",", ":"))
            manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "mixed aggregate host gate"):
                validator.validate(manifest, expected_prefix_sha256=prefix_hash)

    def test_prefix_mutation_is_rejected_before_artifact_trust(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            manifest, prefix_hash = build_complete_fixture(Path(temporary_name))
            lines = manifest.read_text().splitlines()
            first = json.loads(lines[0])
            first["host_seconds"] = 3.2
            lines[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
            manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "frozen 254-row prefix"):
                validator.validate(manifest, expected_prefix_sha256=prefix_hash)


class Cap60WrapperTests(unittest.TestCase):
    def test_wrapper_rejects_host_gate_override(self) -> None:
        completed = subprocess.run(
            [str(CAP60_WRAPPER), "--host-seconds", "30"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 64)
        self.assertIn("owns --host-seconds", completed.stderr)

    def test_wrapper_is_locked_to_cap_60_and_current_inputs(self) -> None:
        body = CAP60_WRAPPER.read_text(encoding="utf-8")
        self.assertIn('exec python3 scripts/run_known_class_embedding_census.py "$@" --host-seconds 60', body)
        for relative in (
            "scripts/run_known_class_embedding_census.py",
            "scripts/enumerate_core_embeddings_bitset.py",
            "scripts/enumerate_core_embeddings_networkx.py",
            "sources/r55_42some.g6",
        ):
            self.assertIn(sha(ROOT / relative), body)


if __name__ == "__main__":
    unittest.main()
