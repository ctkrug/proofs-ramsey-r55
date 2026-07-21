#!/usr/bin/env python3
"""Independent auditor for a four-variable physical-CNF cube manifest.

This checker deliberately imports no project generator.  It reconstructs the
edge-variable ordering, the complete 16-assignment cover, and every virtual
leaf byte stream directly from the retained parent CNF and the JSON manifest.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
from typing import BinaryIO


EXPECTED_PATHS = {
    (6, 2): [[1, 3], [1, 4], [2, 4], [2, 5]],
    (42, 20): [[1, 21], [2, 21], [2, 22], [3, 22]],
}


def sha256_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def open_binary(path: Path) -> BinaryIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rb")
    return path.open("rb")


def edge_variable(u: int, v: int) -> int:
    if u == v:
        raise ValueError("loop is not an edge variable")
    low, high = sorted((u, v))
    return high * (high - 1) // 2 + low + 1


def expected_map(order: int) -> list[str]:
    return [
        f"{edge_variable(low, high)}\t{low}\t{high}"
        for high in range(1, order)
        for low in range(high)
    ]


def read_parent(path: Path) -> tuple[bytes, bytes, int, int, str, str]:
    whole = hashlib.sha256()
    body = hashlib.sha256()
    with open_binary(path) as stream:
        header = stream.readline()
        fields = header.decode("ascii").split()
        if len(fields) != 4 or fields[:2] != ["p", "cnf"]:
            raise AssertionError("malformed parent DIMACS header")
        variables, clauses = map(int, fields[2:])
        whole.update(header)
        count = 0
        chunks: list[bytes] = []
        for line in stream:
            if not line.endswith(b" 0\n") and line != b"0\n":
                raise AssertionError("malformed parent clause")
            whole.update(line)
            body.update(line)
            chunks.append(line)
            count += 1
    if count != clauses:
        raise AssertionError("parent clause count mismatch")
    return header, b"".join(chunks), variables, clauses, whole.hexdigest(), body.hexdigest()


def leaf_hash(body: bytes, variables: int, clauses: int, suffix: list[bytes]) -> str:
    hasher = hashlib.sha256()
    hasher.update(f"p cnf {variables} {clauses + len(suffix)}\n".encode("ascii"))
    hasher.update(body)
    for line in suffix:
        hasher.update(line)
    return hasher.hexdigest()


def canonical_leaf(bits: tuple[int, ...], variables: list[int]) -> tuple[list[int], list[bytes]]:
    literals = [variable if bit else -variable for bit, variable in zip(bits, variables)]
    suffix = [f"{literal} 0\n".encode("ascii") for literal in literals]
    return literals, suffix


def orbit_classes() -> list[list[str]]:
    """Classes under reversal of the declared four-edge P5 path only."""
    unseen = {"".join(map(str, bits)) for bits in itertools.product((0, 1), repeat=4)}
    classes: list[list[str]] = []
    while unseen:
        word = min(unseen)
        orbit = sorted({word, word[::-1]})
        classes.append(orbit)
        unseen.difference_update(orbit)
    return classes


def validate_payload(
    payload: dict[str, object],
    order: int,
    degree_q: int,
    parent_variables: int,
    parent_clauses: int,
    parent_sha256: str,
    parent_body_sha256: str,
    map_sha256: str,
    body: bytes,
) -> dict[str, object]:
    if payload.get("schema_version") != 1:
        raise AssertionError("manifest schema mismatch")
    if payload.get("order") != order or payload.get("degree_q") != degree_q:
        raise AssertionError("manifest parameter mismatch")
    if order != 2 * degree_q + 2:
        raise AssertionError("fixed-root parameter identity failed")
    primary = order * (order - 1) // 2
    if parent_variables < primary:
        raise AssertionError("parent omits primary variables")

    parent = payload.get("parent")
    if not isinstance(parent, dict):
        raise AssertionError("missing parent record")
    expected_parent = {
        "variables": parent_variables,
        "clauses": parent_clauses,
        "uncompressed_sha256": parent_sha256,
        "body_sha256": parent_body_sha256,
        "map_sha256": map_sha256,
    }
    for key, value in expected_parent.items():
        if parent.get(key) != value:
            raise AssertionError(f"parent identity mismatch: {key}")

    declared_edges = payload.get("path_edges")
    expected_edges = EXPECTED_PATHS.get((order, degree_q))
    if declared_edges != expected_edges:
        raise AssertionError("declared deterministic path mismatch")
    variables = [edge_variable(*edge) for edge in expected_edges]
    if payload.get("path_variables") != variables:
        raise AssertionError("path variable arithmetic mismatch")
    if len(set(variables)) != 4 or any(variable > primary for variable in variables):
        raise AssertionError("path variables are not four distinct primaries")
    left = set(range(1, degree_q + 1))
    right = set(range(degree_q + 1, order))
    root_units = {edge_variable(0, vertex) for vertex in range(1, order)}
    for u, v in expected_edges:
        if not ((u in left and v in right) or (u in right and v in left)):
            raise AssertionError("path edge is not cross-part")
        if edge_variable(u, v) in root_units:
            raise AssertionError("path edge is a fixed root unit")

    leaves = payload.get("leaves")
    if not isinstance(leaves, list) or len(leaves) != 16:
        raise AssertionError("manifest does not contain exactly 16 leaves")
    seen: set[tuple[int, ...]] = set()
    reconstructed_hashes: dict[str, str] = {}
    for leaf in leaves:
        if not isinstance(leaf, dict):
            raise AssertionError("leaf record is not an object")
        bits_raw = leaf.get("bits")
        if not isinstance(bits_raw, list) or len(bits_raw) != 4 or any(bit not in (0, 1) for bit in bits_raw):
            raise AssertionError("invalid cube bits")
        bits = tuple(int(bit) for bit in bits_raw)
        if bits in seen:
            raise AssertionError("duplicate cube assignment")
        seen.add(bits)
        leaf_id = "".join(map(str, bits))
        if leaf.get("id") != leaf_id:
            raise AssertionError("noncanonical leaf id")
        literals, suffix = canonical_leaf(bits, variables)
        if leaf.get("literals") != literals:
            raise AssertionError("cube literal/sign mismatch")
        suffix_hash = hashlib.sha256(b"".join(suffix)).hexdigest()
        if leaf.get("suffix_sha256") != suffix_hash:
            raise AssertionError("cube suffix hash mismatch")
        expected_hash = leaf_hash(body, parent_variables, parent_clauses, suffix)
        if leaf.get("leaf_uncompressed_sha256") != expected_hash:
            raise AssertionError("virtual leaf hash mismatch")
        if leaf.get("clauses") != parent_clauses + 4:
            raise AssertionError("leaf clause count mismatch")
        reconstructed_hashes[leaf_id] = expected_hash
    expected_assignments = set(itertools.product((0, 1), repeat=4))
    if seen != expected_assignments:
        raise AssertionError("cube cover is not exhaustive")
    pairs = 0
    ordered = sorted(seen)
    for index, first in enumerate(ordered):
        for second in ordered[index + 1 :]:
            if not any(a != b for a, b in zip(first, second)):
                raise AssertionError("distinct cubes are not disjoint")
            pairs += 1
    classes = orbit_classes()
    if payload.get("path_reversal_orbit_classes") != classes:
        raise AssertionError("path-reversal orbit ledger mismatch")
    return {
        "assignments": len(seen),
        "pairwise_disjoint_pairs": pairs,
        "exhaustive": seen == expected_assignments,
        "path_variables": variables,
        "root_unit_variables_disjoint": set(variables).isdisjoint(root_units),
        "path_reversal_orbit_count": len(classes),
        "path_reversal_orbit_classes": classes,
        "leaf_hashes": reconstructed_hashes,
    }


def mutation_gate(
    payload: dict[str, object],
    validate,
) -> dict[str, bool]:
    mutations: dict[str, dict[str, object]] = {}
    missing = copy.deepcopy(payload)
    missing["leaves"] = missing["leaves"][:-1]
    mutations["missing_cube"] = missing
    duplicate = copy.deepcopy(payload)
    duplicate["leaves"][-1] = copy.deepcopy(duplicate["leaves"][0])
    mutations["duplicate_cube"] = duplicate
    sign = copy.deepcopy(payload)
    sign["leaves"][0]["literals"][0] *= -1
    mutations["cube_sign_reversal"] = sign
    repeated = copy.deepcopy(payload)
    repeated["path_variables"][1] = repeated["path_variables"][0]
    mutations["repeated_variable"] = repeated
    shifted = copy.deepcopy(payload)
    shifted["path_variables"][0] += 1
    mutations["shifted_variable"] = shifted
    auxiliary = copy.deepcopy(payload)
    auxiliary["path_variables"][0] = int(payload["parent"]["variables"])
    mutations["auxiliary_variable"] = auxiliary
    root = copy.deepcopy(payload)
    root["path_edges"][0] = [0, 1]
    mutations["root_unit_variable"] = root
    body = copy.deepcopy(payload)
    body["parent"]["body_sha256"] = "0" * 64
    mutations["parent_body_drift"] = body
    target = copy.deepcopy(payload)
    target["leaves"][0]["leaf_uncompressed_sha256"] = payload["parent"]["uncompressed_sha256"]
    mutations["proof_target_parent_substitution"] = target

    results: dict[str, bool] = {}
    for name, candidate in mutations.items():
        try:
            validate(candidate)
        except (AssertionError, KeyError, TypeError, ValueError):
            results[name] = True
        else:
            results[name] = False
    if not all(results.values()):
        raise AssertionError("a manifest mutation escaped detection")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--map", dest="mapping", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("audit report already exists")
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    order = int(payload["order"])
    degree_q = int(payload["degree_q"])
    map_lines = args.mapping.read_text(encoding="ascii").splitlines()
    if map_lines != expected_map(order):
        raise AssertionError("independently reconstructed full edge map mismatch")
    map_sha256 = sha256_path(args.mapping)
    _, body, variables, clauses, whole_sha256, body_sha256 = read_parent(args.parent)

    def validate(candidate: dict[str, object]) -> dict[str, object]:
        return validate_payload(
            candidate,
            order,
            degree_q,
            variables,
            clauses,
            whole_sha256,
            body_sha256,
            map_sha256,
            body,
        )

    cover = validate(payload)
    mutations = mutation_gate(payload, validate)
    report = {
        "status": "cube_manifest_audit_pass",
        "scope": payload.get("scope"),
        "parent_uncompressed_sha256": whole_sha256,
        "parent_body_sha256": body_sha256,
        "parent_variables": variables,
        "parent_clauses": clauses,
        "full_map_reconstructed_independently": True,
        "physical_leaf_contract": "parent body with replaced clause-count header plus four final unit clauses",
        "cover": cover,
        "mutation_rejections": mutations,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
