#!/usr/bin/env python3
"""Build and verify the deterministic, metadata-only R(5,5) outreach packet.

The packet does not copy evidence.  Its three path lists are exact allowlists of
files already committed in the repository, and MANIFEST.sha256 binds those
files plus the packet metadata.  A packet is therefore built only after its
evidence revision is committed, then committed itself in a following revision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Iterable


SCHEMA_VERSION = 1
PACKET_NAMES = ("packet-a", "packet-b", "packet-c")
NONCLAIMS = (
    "This packet does not claim a new Ramsey graph.",
    "This packet does not change the bound 43 <= R(5,5) <= 46.",
    "This packet does not claim that the supplied 656-graph corpus is complete.",
    "This packet does not claim to reproduce BigCompute's 656/656 run.",
    "This packet is not peer review.",
)
TOOL_DISCLOSURE = (
    "Python, GCC, CaDiCaL, Z3, nauty, NetworkX, drat-trim, and AI assistance were used "
    "in the research and verification workflow; the exact role of each tool remains "
    "limited to the checked artifacts that record it."
)
SHA_LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")
REVISION_LINE = re.compile(r"^Evidence revision: `([0-9a-f]{40,64})`$")
SPEC_LINE = re.compile(r"^Packet specification: `([^`]+)`$")


class PacketError(RuntimeError):
    pass


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PacketError(f"git {' '.join(args)} failed: {detail}")
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PacketError(f"{label} must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/") or any(part in {"", ".", ".."} for part in path.parts):
        raise PacketError(f"unsafe {label}: {value!r}")
    normalized = path.as_posix()
    if normalized != value.rstrip("/"):
        raise PacketError(f"non-canonical {label}: {value!r}")
    return normalized


def load_spec(path: Path) -> dict[str, object]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PacketError(f"cannot read packet spec: {exc}") from exc
    if not isinstance(spec, dict) or spec.get("schema_version") != SCHEMA_VERSION:
        raise PacketError(f"packet spec must have schema_version {SCHEMA_VERSION}")
    if spec.get("packet_names") != list(PACKET_NAMES):
        raise PacketError(f"packet_names must be exactly {list(PACKET_NAMES)!r}")
    safe_relative(spec.get("output"), label="output")
    packets = spec.get("packets")
    if (
        not isinstance(packets, list)
        or any(not isinstance(packet, dict) for packet in packets)
        or [packet.get("name") for packet in packets] != list(PACKET_NAMES)
    ):
        raise PacketError("spec must define packet-a, packet-b, and packet-c exactly once in order")
    return spec


def committed_paths(repo: Path) -> set[str]:
    result = run_git(repo, "ls-files", "-z")
    return {item for item in result.stdout.split("\0") if item}


def ensure_no_symlink_components(repo: Path, path: str) -> None:
    cursor = repo
    for part in PurePosixPath(path).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise PacketError(f"path contains a symlink component: {path}")


def ensure_regular_committed(repo: Path, path: str, tracked: set[str], revision: str) -> None:
    if path not in tracked:
        raise PacketError(f"selected path is not tracked: {path}")
    ensure_no_symlink_components(repo, path)
    full = repo / path
    try:
        mode = full.lstat().st_mode
    except FileNotFoundError as exc:
        raise PacketError(f"selected path is absent: {path}") from exc
    if stat.S_ISLNK(mode):
        raise PacketError(f"selected path is a symlink: {path}")
    if not stat.S_ISREG(mode):
        raise PacketError(f"selected path is not a regular file: {path}")
    status = run_git(repo, "status", "--porcelain=v1", "--untracked-files=all", "--", path).stdout
    if status:
        raise PacketError(f"selected path has uncommitted state: {path}")
    diff = run_git(repo, "diff", "--quiet", revision, "--", path, check=False)
    if diff.returncode != 0:
        raise PacketError(f"selected path differs from evidence revision {revision}: {path}")


def expand_entry(repo: Path, entry: object, tracked: set[str], revision: str) -> list[str]:
    if not isinstance(entry, dict) or set(entry) != {"kind", "path"}:
        raise PacketError("each include entry must contain exactly kind and path")
    kind = entry["kind"]
    path = safe_relative(entry["path"], label="include path")
    if kind == "file":
        selected = [path]
    elif kind == "tree":
        prefix = path + "/"
        selected = sorted(item for item in tracked if item.startswith(prefix))
        if not selected:
            raise PacketError(f"tracked tree is empty or absent: {path}")
        tree_status = run_git(
            repo, "status", "--porcelain=v1", "--untracked-files=all", "--", path
        ).stdout
        if tree_status:
            raise PacketError(f"selected tree has uncommitted state: {path}")
    else:
        raise PacketError(f"unsupported include kind: {kind!r}")
    for selected_path in selected:
        ensure_regular_committed(repo, selected_path, tracked, revision)
    return selected


def resolve_revision(repo: Path, revision: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40,64}", revision):
        raise PacketError("revision must be a full lowercase hexadecimal object id")
    resolved = run_git(repo, "rev-parse", f"{revision}^{{commit}}").stdout.strip()
    if resolved != revision:
        raise PacketError(f"revision did not resolve byte-for-byte: {revision}")
    return resolved


def expand_packets(repo: Path, spec: dict[str, object], revision: str) -> dict[str, list[str]]:
    tracked = committed_paths(repo)
    expanded: dict[str, list[str]] = {}
    for packet in spec["packets"]:  # type: ignore[index]
        assert isinstance(packet, dict)
        name = packet["name"]
        if not isinstance(packet.get("title"), str) or not packet["title"]:
            raise PacketError(f"{name} requires a title")
        if not isinstance(packet.get("scope"), str) or not packet["scope"]:
            raise PacketError(f"{name} requires a scope")
        includes = packet.get("include")
        inherits = packet.get("inherits", [])
        hooks = packet.get("semantic_replay", [])
        if not isinstance(includes, list) or not includes:
            raise PacketError(f"{name} requires a non-empty include list")
        if not isinstance(inherits, list) or any(parent not in expanded for parent in inherits):
            raise PacketError(f"{name} inherits only earlier declared packets")
        if not isinstance(hooks, list) or not hooks or any(not isinstance(hook, str) or not hook.strip() for hook in hooks):
            raise PacketError(f"{name} requires non-empty semantic replay hooks")
        paths: set[str] = set()
        for parent in inherits:
            paths.update(expanded[parent])
        for entry in includes:
            paths.update(expand_entry(repo, entry, tracked, revision))
        expanded[name] = sorted(paths)
    return expanded


def render_readme(
    spec: dict[str, object], revision: str, spec_relative: str, expanded: dict[str, list[str]]
) -> str:
    lines = [
        "# R(5,5) alignment packet",
        "",
        f"Evidence revision: `{revision}`",
        f"Packet specification: `{spec_relative}`",
        "",
        "This is a deterministic index of committed evidence. The three `.paths` files are the exact",
        "scope boundaries; `MANIFEST.sha256` binds every selected file and this metadata.",
        "",
        "## Non-claims",
        "",
    ]
    lines.extend(f"- {statement}" for statement in NONCLAIMS)
    lines.extend(["", "## Tool and AI disclosure", "", TOOL_DISCLOSURE, ""])
    packets_by_name = {packet["name"]: packet for packet in spec["packets"]}  # type: ignore[index]
    for name in PACKET_NAMES:
        packet = packets_by_name[name]
        lines.extend(
            [
                f"## {packet['title']}",
                "",
                str(packet["scope"]),
                "",
                f"Exact allowlist: `{name}.paths` ({len(expanded[name])} files).",
                "",
                "Semantic replay hooks:",
                "",
            ]
        )
        for hook in packet["semantic_replay"]:
            lines.extend(["```bash", str(hook), "```", ""])
    output = safe_relative(spec["output"], label="output")
    lines.extend(
        [
            "## Integrity and detached clean-clone recheck",
            "",
            "From the repository root at the packet commit:",
            "",
            "```bash",
            f"python3 scripts/build_r55_outreach_packet.py verify --packet {output}",
            "```",
            "",
            "From any trusted checkout, replace the two placeholders with the immutable repository URL",
            "and packet commit (not a branch):",
            "",
            "```bash",
            "python3 scripts/build_r55_outreach_packet.py clean-clone-recheck \\",
            "  --repository REPOSITORY_URL --packet-revision PACKET_COMMIT \\",
            f"  --packet {output}",
            "```",
            "",
            "Hash verification is structural only. The commands above under each packet are the semantic",
            "checks and remain limited to their stated scopes.",
            "",
        ]
    )
    return "\n".join(lines)


def manifest_paths(
    output_relative: str, spec_relative: str, expanded: dict[str, list[str]]
) -> list[str]:
    metadata = [f"{output_relative}/README.md"] + [
        f"{output_relative}/{name}.paths" for name in PACKET_NAMES
    ]
    return sorted({spec_relative, *metadata}.union(*(set(paths) for paths in expanded.values())))


def build(repo: Path, spec_path: Path, output_arg: str | None, revision: str) -> Path:
    repo = repo.resolve()
    revision = resolve_revision(repo, revision)
    spec_path = spec_path.resolve()
    try:
        spec_relative = safe_relative(
            spec_path.relative_to(repo).as_posix(), label="spec path"
        )
    except ValueError as exc:
        raise PacketError("packet spec must be inside the repository") from exc
    tracked = committed_paths(repo)
    ensure_regular_committed(repo, spec_relative, tracked, revision)
    spec = load_spec(spec_path)
    configured_output = safe_relative(spec["output"], label="output")
    output_relative = safe_relative(output_arg or configured_output, label="output")
    if output_relative != configured_output:
        raise PacketError(f"output must match spec exactly: {configured_output}")
    output = repo / output_relative
    if output.exists():
        raise PacketError(f"refusing to overwrite existing packet: {output_relative}")
    expanded = expand_packets(repo, spec, revision)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        for name in PACKET_NAMES:
            (staging / f"{name}.paths").write_text(
                "".join(f"{path}\n" for path in expanded[name]), encoding="utf-8"
            )
        (staging / "README.md").write_text(
            render_readme(spec, revision, spec_relative, expanded), encoding="utf-8"
        )
        lines = []
        for relative in manifest_paths(output_relative, spec_relative, expanded):
            actual = staging / Path(relative).relative_to(output_relative) if relative.startswith(output_relative + "/") else repo / relative
            lines.append(f"{sha256(actual)}  {relative}\n")
        (staging / "MANIFEST.sha256").write_text("".join(lines), encoding="utf-8")
        os.replace(staging, output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output


def parse_readme_contract(readme: Path) -> tuple[str, str]:
    revision_matches = []
    spec_matches = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        if match := REVISION_LINE.fullmatch(line):
            revision_matches.append(match.group(1))
        if match := SPEC_LINE.fullmatch(line):
            spec_matches.append(match.group(1))
    if len(revision_matches) != 1 or len(spec_matches) != 1:
        raise PacketError("README must contain one exact evidence revision and packet specification")
    return revision_matches[0], safe_relative(spec_matches[0], label="spec path")


def read_path_list(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines != sorted(set(lines)):
        raise PacketError(f"path list must be non-empty, sorted, and duplicate-free: {path.name}")
    return [safe_relative(line, label=f"{path.name} entry") for line in lines]


def verify(repo: Path, packet_arg: str) -> None:
    repo = repo.resolve()
    packet_relative = safe_relative(packet_arg, label="packet")
    packet = repo / packet_relative
    ensure_no_symlink_components(repo, packet_relative)
    if packet.is_symlink() or not packet.is_dir():
        raise PacketError(f"packet directory is absent or a symlink: {packet_relative}")
    expected_names = {"README.md", "MANIFEST.sha256", *(f"{name}.paths" for name in PACKET_NAMES)}
    actual_names = {item.name for item in packet.iterdir()}
    if actual_names != expected_names:
        raise PacketError(f"packet contents differ from exact contract: {sorted(actual_names)}")
    readme_text = (packet / "README.md").read_text(encoding="utf-8")
    for statement in NONCLAIMS:
        if readme_text.count(statement) != 1:
            raise PacketError(f"README non-claim missing or duplicated: {statement}")
    if readme_text.count(TOOL_DISCLOSURE) != 1:
        raise PacketError("README tool/AI disclosure missing or duplicated")
    recorded_revision, spec_relative = parse_readme_contract(packet / "README.md")
    revision = resolve_revision(repo, recorded_revision)
    tracked = committed_paths(repo)
    ensure_regular_committed(repo, spec_relative, tracked, revision)
    spec = load_spec(repo / spec_relative)
    if safe_relative(spec["output"], label="output") != packet_relative:
        raise PacketError("packet path does not match its committed specification")
    declared = expand_packets(repo, spec, revision)
    selected: set[str] = set()
    for name in PACKET_NAMES:
        observed_paths = read_path_list(packet / f"{name}.paths")
        if observed_paths != declared[name]:
            raise PacketError(f"{name}.paths differs from its committed allowlist")
        selected.update(observed_paths)
    for path in sorted(selected):
        ensure_regular_committed(repo, path, tracked, revision)
    expected_manifest = set(manifest_paths(packet_relative, spec_relative, declared))
    observed: dict[str, str] = {}
    for line in (packet / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        match = SHA_LINE.fullmatch(line)
        if not match:
            raise PacketError(f"malformed manifest line: {line!r}")
        digest, relative = match.groups()
        relative = safe_relative(relative, label="manifest path")
        if relative in observed:
            raise PacketError(f"duplicate manifest path: {relative}")
        observed[relative] = digest
    if set(observed) != expected_manifest:
        raise PacketError("manifest path set does not exactly match the packet allowlists and metadata")
    for relative, expected_digest in sorted(observed.items()):
        ensure_no_symlink_components(repo, relative)
        path = repo / relative
        if path.is_symlink() or not path.is_file():
            raise PacketError(f"manifest target is absent, non-regular, or a symlink: {relative}")
        if sha256(path) != expected_digest:
            raise PacketError(f"manifest hash mismatch: {relative}")


def clean_clone_recheck(repository: str, packet_revision: str, packet: str) -> None:
    safe_relative(packet, label="packet")
    if not re.fullmatch(r"[0-9a-f]{40,64}", packet_revision):
        raise PacketError("packet revision must be a full lowercase hexadecimal object id")
    with tempfile.TemporaryDirectory(prefix="r55-outreach-recheck-") as temp:
        clone = Path(temp) / "repo"
        subprocess.run(["git", "clone", "--quiet", "--no-checkout", repository, str(clone)], check=True)
        resolved = run_git(clone, "rev-parse", f"{packet_revision}^{{commit}}").stdout.strip()
        if resolved != packet_revision:
            raise PacketError("packet revision did not resolve byte-for-byte in the clone")
        run_git(clone, "checkout", "--quiet", "--detach", packet_revision)
        verify(clone, packet)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__)
    sub = top.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--repo", default=".")
    build_parser.add_argument("--spec", default="docs/r55-outreach-packet-spec.json")
    build_parser.add_argument("--output")
    build_parser.add_argument("--revision", required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--repo", default=".")
    verify_parser.add_argument("--packet", default="outreach/r55-alignment-20260721")
    clone_parser = sub.add_parser("clean-clone-recheck")
    clone_parser.add_argument("--repository", required=True)
    clone_parser.add_argument("--packet-revision", required=True)
    clone_parser.add_argument("--packet", default="outreach/r55-alignment-20260721")
    return top


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build":
            repo = Path(args.repo)
            spec_path = Path(args.spec)
            if not spec_path.is_absolute():
                spec_path = repo / spec_path
            output = build(repo, spec_path, args.output, args.revision)
            print(json.dumps({"status": "built", "packet": str(output)}, sort_keys=True))
        elif args.command == "verify":
            verify(Path(args.repo), args.packet)
            print(json.dumps({"status": "verified", "packet": args.packet}, sort_keys=True))
        else:
            clean_clone_recheck(args.repository, args.packet_revision, args.packet)
            print(json.dumps({"status": "verified-clean-clone", "packet": args.packet}, sort_keys=True))
    except (PacketError, OSError, subprocess.CalledProcessError) as exc:
        print(f"outreach-packet: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
