from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_r55_outreach_packet.py"
MODULE_SPEC = importlib.util.spec_from_file_location("r55_packet", SCRIPT)
assert MODULE_SPEC and MODULE_SPEC.loader
packet = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(packet)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, text=True, capture_output=True
    ).stdout.strip()


class OutreachPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "Packet Test")
        (self.repo / "scripts").mkdir()
        shutil.copy2(SCRIPT, self.repo / "scripts" / SCRIPT.name)
        for name, body in {
            "a/evidence.txt": "a\n",
            "b/evidence.txt": "b\n",
            "c/evidence.txt": "c\n",
        }.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        self.spec_path = self.repo / "spec.json"
        self.spec_path.write_text(json.dumps(self.make_spec(), indent=2) + "\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "fixture")
        self.revision = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def make_spec() -> dict[str, object]:
        return {
            "schema_version": 1,
            "packet_names": ["packet-a", "packet-b", "packet-c"],
            "output": "outreach/r55-alignment-20260721",
            "packets": [
                {
                    "name": "packet-a",
                    "title": "Packet A",
                    "scope": "A scope.",
                    "inherits": [],
                    "include": [{"kind": "tree", "path": "a"}],
                    "semantic_replay": ["python3 -c \"print('a')\""],
                },
                {
                    "name": "packet-b",
                    "title": "Packet B",
                    "scope": "B scope.",
                    "inherits": [],
                    "include": [{"kind": "file", "path": "b/evidence.txt"}],
                    "semantic_replay": ["python3 -c \"print('b')\""],
                },
                {
                    "name": "packet-c",
                    "title": "Packet C",
                    "scope": "C scope.",
                    "inherits": ["packet-a"],
                    "include": [{"kind": "file", "path": "c/evidence.txt"}],
                    "semantic_replay": ["python3 -c \"print('c')\""],
                },
            ],
        }

    def build(self) -> Path:
        return packet.build(self.repo, self.spec_path, None, self.revision)

    def test_build_is_deterministic_and_c_inherits_a(self) -> None:
        first = self.build()
        first_bytes = {path.name: path.read_bytes() for path in first.iterdir()}
        self.assertEqual(
            (first / "packet-c.paths").read_text().splitlines(),
            ["a/evidence.txt", "c/evidence.txt"],
        )
        shutil.rmtree(first)
        second = self.build()
        self.assertEqual(first_bytes, {path.name: path.read_bytes() for path in second.iterdir()})

    def test_readme_has_exact_nonclaims_disclosure_and_hooks(self) -> None:
        readme = (self.build() / "README.md").read_text(encoding="utf-8")
        for statement in packet.NONCLAIMS:
            self.assertEqual(readme.count(statement), 1)
        self.assertEqual(readme.count(packet.TOOL_DISCLOSURE), 1)
        self.assertIn("Semantic replay hooks", readme)
        self.assertIn("clean-clone-recheck", readme)

    def test_rejects_absolute_parent_and_symlink_paths(self) -> None:
        for bad in ("/etc/passwd", "../outside", "a/../b/evidence.txt"):
            with self.subTest(bad=bad):
                with self.assertRaises(packet.PacketError):
                    packet.safe_relative(bad, label="test")
        link = self.repo / "a" / "link"
        link.symlink_to("evidence.txt")
        git(self.repo, "add", "a/link")
        git(self.repo, "commit", "-qm", "track symlink")
        revision = git(self.repo, "rev-parse", "HEAD")
        with self.assertRaisesRegex(packet.PacketError, "symlink"):
            packet.expand_packets(self.repo, packet.load_spec(self.spec_path), revision)

    def test_rejects_untracked_or_dirty_selected_content(self) -> None:
        (self.repo / "a" / "untracked.txt").write_text("no\n", encoding="utf-8")
        with self.assertRaisesRegex(packet.PacketError, "uncommitted"):
            self.build()
        (self.repo / "a" / "untracked.txt").unlink()
        (self.repo / "b" / "evidence.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(packet.PacketError, "uncommitted"):
            self.build()

    def test_verify_detects_tamper_and_extra_packet_file(self) -> None:
        output = self.build()
        packet.verify(self.repo, "outreach/r55-alignment-20260721")
        (self.repo / "a" / "evidence.txt").write_text("tampered\n", encoding="utf-8")
        with self.assertRaises(packet.PacketError):
            packet.verify(self.repo, "outreach/r55-alignment-20260721")
        git(self.repo, "checkout", "--", "a/evidence.txt")
        (output / "extra.txt").write_text("extra\n", encoding="utf-8")
        with self.assertRaisesRegex(packet.PacketError, "exact contract"):
            packet.verify(self.repo, "outreach/r55-alignment-20260721")

    def test_manifest_exactly_covers_allowlists_and_metadata(self) -> None:
        output = self.build()
        manifest_paths = {
            line.split("  ", 1)[1]
            for line in (output / "MANIFEST.sha256").read_text().splitlines()
        }
        self.assertEqual(
            manifest_paths,
            {
                "a/evidence.txt",
                "b/evidence.txt",
                "c/evidence.txt",
                "spec.json",
                "outreach/r55-alignment-20260721/README.md",
                "outreach/r55-alignment-20260721/packet-a.paths",
                "outreach/r55-alignment-20260721/packet-b.paths",
                "outreach/r55-alignment-20260721/packet-c.paths",
            },
        )

    def test_verify_enforces_committed_allowlist_even_with_consistent_hashes(self) -> None:
        output = self.build()
        path_list = output / "packet-a.paths"
        path_list.write_text("a/evidence.txt\nc/evidence.txt\n", encoding="utf-8")
        manifest = output / "MANIFEST.sha256"
        lines = []
        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ", 1)
            if relative.endswith("/packet-a.paths"):
                digest = packet.sha256(path_list)
            lines.append(f"{digest}  {relative}\n")
        manifest.write_text("".join(lines), encoding="utf-8")
        with self.assertRaisesRegex(packet.PacketError, "committed allowlist"):
            packet.verify(self.repo, "outreach/r55-alignment-20260721")

    def test_clean_clone_detached_recheck(self) -> None:
        self.build()
        git(self.repo, "add", "outreach")
        git(self.repo, "commit", "-qm", "packet")
        packet_revision = git(self.repo, "rev-parse", "HEAD")
        packet.clean_clone_recheck(
            str(self.repo), packet_revision, "outreach/r55-alignment-20260721"
        )


if __name__ == "__main__":
    unittest.main()
