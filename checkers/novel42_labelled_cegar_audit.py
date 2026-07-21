#!/usr/bin/env python3
"""Cold audit for the one-boundary labelled-model CEGAR packet.

This file imports no producer code.  It independently maps the 426 primary
variables, evaluates every retained total assignment against the immutable
base CNF and all earlier blocks, checks graph semantics with NetworkX, and
uses NetworkX isomorphism to confirm each nauty-identified supplied target.
"""

from __future__ import annotations

import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sys

import networkx as nx


ORDER = 42
TOTAL_VARIABLES = 155_976
PRIMARY_VARIABLES = 426
BASE_CLAUSES = 508_157
SOURCE_RECORD = 21
MINIMUM_DISTANCE = 60
FINGERPRINT = "r55novel42basin2026"
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"
BASE_LOGICAL_SHA256 = "2f1c3b2ac59e4c4b6e2873d2d5ebb2d2eba4fd908a2927f2a30d1936bc3d1072"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def logical_digest(path: Path) -> str:
    value = hashlib.sha256()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def stable_destroy() -> list[int]:
    population = list(range(ORDER))
    ranked = sorted(
        population,
        key=lambda item: hashlib.sha256(f"{FINGERPRINT}:destroy:{SOURCE_RECORD - 1}:{item}".encode()).digest(),
    )
    return sorted(ranked[:12])


def bit(packed: bytes, variable: int) -> bool:
    position = variable - 1
    return bool((packed[position // 8] >> (position % 8)) & 1)


def literal_true(packed: bytes, literal: int) -> bool:
    value = bit(packed, abs(literal))
    return value if literal > 0 else not value


def parse_blocks(path: Path) -> list[list[int]]:
    blocks: list[list[int]] = []
    for line_number, raw in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        literals = [int(text) for text in raw.split()]
        if len(literals) != PRIMARY_VARIABLES + 1 or literals[-1] != 0:
            raise AssertionError(f"malformed primary block at line {line_number}")
        literals.pop()
        if sorted(map(abs, literals)) != list(range(1, PRIMARY_VARIABLES + 1)):
            raise AssertionError("block does not contain each primary variable once")
        blocks.append(literals)
    return blocks


def evaluate_base(path: Path, packed: bytes) -> None:
    variables = expected = counted = None
    count = 0
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as stream:
        for line_number, raw in enumerate(stream, 1):
            if raw.startswith("p cnf "):
                _, _, variables_text, clauses_text = raw.split()
                variables, expected = int(variables_text), int(clauses_text)
                continue
            if not raw.strip() or raw.startswith("c"):
                continue
            literals = [int(text) for text in raw.split()]
            if not literals or literals[-1] != 0:
                raise AssertionError(f"malformed base CNF line {line_number}")
            literals.pop()
            if not any(literal_true(packed, literal) for literal in literals):
                raise AssertionError(f"total model falsifies base clause at line {line_number}")
            count += 1
    if (variables, expected, count) != (TOTAL_VARIABLES, BASE_CLAUSES, BASE_CLAUSES):
        raise AssertionError("base CNF counts disagree")


def validate_ramsey(candidate: nx.Graph) -> tuple[int, int]:
    omega = max(map(len, nx.find_cliques(candidate)), default=0)
    alpha = max(map(len, nx.find_cliques(nx.complement(candidate))), default=0)
    if omega >= 5 or alpha >= 5:
        raise AssertionError("candidate fails independent maximal-clique scan")
    return omega, alpha


def destroy_permutation_normal_form(candidate: nx.Graph, destroy: list[int]) -> tuple[bool, str | None]:
    """Canonicalize the S_12 action when all core-neighborhood rows differ."""
    fixed = sorted(set(range(ORDER)) - set(destroy))
    ranked = sorted((tuple(int(candidate.has_edge(v, u)) for u in fixed), v) for v in destroy)
    rows_distinct = len({row for row, _ in ranked}) == len(destroy)
    if not rows_distinct:
        return False, None
    old_for_new = {new: old for new, (_, old) in zip(sorted(destroy), ranked, strict=True)}
    old_for_new.update({v: v for v in fixed})
    bits = bytes(
        int(candidate.has_edge(old_for_new[low], old_for_new[high]))
        for high in range(1, ORDER)
        for low in range(high)
        if low in set(destroy) or high in set(destroy)
    )
    return True, hashlib.sha256(bits).hexdigest()


def main() -> int:
    if len(sys.argv) != 6:
        raise SystemExit("usage: novel42_labelled_cegar_audit.py CORPUS CORPUS_REPORT PRODUCTION_REPORT ARTIFACT_DIR OUTPUT")
    corpus_path, corpus_report_path, production_path, artifact_dir, output = map(Path, sys.argv[1:])
    if digest(corpus_path) != CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")
    retained = json.loads(corpus_report_path.read_text(encoding="utf-8"))
    production = json.loads(production_path.read_text(encoding="utf-8"))
    base_path = artifact_dir / "base.cnf.gz"
    if logical_digest(base_path) != BASE_LOGICAL_SHA256:
        raise AssertionError("base CNF logical hash mismatch")
    if production["claim_limit"] != "each 426-literal block excludes one labelled completion only; it is not an isomorphism-class block or a boundary exclusion":
        raise AssertionError("production scope wording drifted")
    records = corpus_path.read_bytes().splitlines()
    if len(records) != 328:
        raise AssertionError("corpus record count mismatch")
    sources = [nx.from_graph6_bytes(record) for record in records]
    controls = sources + [nx.complement(graph) for graph in sources]
    source = sources[SOURCE_RECORD - 1]
    destroy = stable_destroy()
    if destroy != production["boundary"]["destroy_vertices"]:
        raise AssertionError("destroy set mismatch")
    destroyed = set(destroy)
    variable_edges = [
        (low, high)
        for high in range(1, ORDER)
        for low in range(high)
        if low in destroyed or high in destroyed
    ]
    if len(variable_edges) != PRIMARY_VARIABLES:
        raise AssertionError("boundary variable mapping mismatch")

    canonical_lookup: dict[str, tuple[int, str, nx.Graph]] = {}
    for entry in retained["per_record_manifest"]:
        record = int(entry["record"])
        canonical_lookup[entry["source_canonical_sha256"]] = (record, "source", sources[record - 1])
        canonical_lookup[entry["complement_canonical_sha256"]] = (record, "complement", controls[328 + record - 1])
    if len(canonical_lookup) != 656:
        raise AssertionError("canonical manifest is not 656 distinct entries")

    blocks = parse_blocks(artifact_dir / "blocks.dimacs")
    models = production["models"]
    expected_blocks = len(models) if production["witness"] is None else len(models) - 1
    if len(blocks) != expected_blocks or len(models) > 64:
        raise AssertionError("model/block stopping state mismatch")
    if production["distinct_primary_vectors"] != len(models):
        raise AssertionError("production distinct-vector count mismatch")

    audited: list[dict[str, object]] = []
    seen_primary: set[str] = set()
    reached: set[tuple[int, str]] = set()
    destroy_normal_forms: set[str] = set()
    for index, entry in enumerate(models):
        round_number = index + 1
        if entry["round"] != round_number:
            raise AssertionError("nonconsecutive model ledger")
        model_path = artifact_dir / f"model-{round_number:03d}.bits"
        candidate_path = artifact_dir / f"candidate-{round_number:03d}.g6"
        canonical_path = artifact_dir / f"candidate-{round_number:03d}.canonical.g6"
        packed = model_path.read_bytes()
        if len(packed) != TOTAL_VARIABLES // 8 or digest(model_path) != entry["model_bits_sha256"]:
            raise AssertionError("packed model size/hash mismatch")
        primary_bytes = bytes(
            sum(
                (1 << bit_index)
                if byte_index * 8 + bit_index + 1 <= PRIMARY_VARIABLES
                and bit(packed, byte_index * 8 + bit_index + 1)
                else 0
                for bit_index in range(8)
            )
            for byte_index in range((PRIMARY_VARIABLES + 7) // 8)
        )
        primary_hash = hashlib.sha256(primary_bytes).hexdigest()
        if primary_hash != entry["primary_vector_sha256"] or primary_hash in seen_primary:
            raise AssertionError("primary projection hash mismatch or duplicate")
        seen_primary.add(primary_hash)
        evaluate_base(base_path, packed)
        if any(not any(literal_true(packed, literal) for literal in block) for block in blocks[:index]):
            raise AssertionError("model fails an earlier blocking clause")

        candidate = nx.from_graph6_bytes(candidate_path.read_bytes().strip())
        if candidate.number_of_nodes() != ORDER:
            raise AssertionError("candidate order mismatch")
        for variable, (u, v) in enumerate(variable_edges, 1):
            if candidate.has_edge(u, v) != bit(packed, variable):
                raise AssertionError("primary model-to-graph mapping mismatch")
        fixed_equal = all(
            candidate.has_edge(u, v) == source.has_edge(u, v)
            for u, v in itertools.combinations(range(ORDER), 2)
            if u not in destroyed and v not in destroyed
        )
        distance = sum(candidate.has_edge(u, v) != source.has_edge(u, v) for u, v in variable_edges)
        if not fixed_equal or distance < MINIMUM_DISTANCE or distance != entry["actual_boundary_hamming_distance"]:
            raise AssertionError("frozen-core or distance mismatch")
        omega, alpha = validate_ramsey(candidate)
        rows_distinct, destroy_normal_form = destroy_permutation_normal_form(candidate, destroy)
        if destroy_normal_form is not None:
            destroy_normal_forms.add(destroy_normal_form)

        canonical_hash = digest(canonical_path)
        target = canonical_lookup.get(canonical_hash)
        if target is None:
            # This expensive path is used only for an alleged corpus nonmember.
            candidate_degrees = sorted(dict(candidate.degree()).values())
            for control in controls:
                if sorted(dict(control.degree()).values()) == candidate_degrees and nx.is_isomorphic(candidate, control):
                    raise AssertionError("alleged canonical nonmember is NetworkX-isomorphic to a supplied control")
            target_label = None
        else:
            target_record, target_kind, target_graph = target
            if not nx.is_isomorphic(candidate, target_graph):
                raise AssertionError("NetworkX rejects the nauty-identified supplied target")
            target_label = {"record": target_record, "kind": target_kind}
            reached.add((target_record, target_kind))
            if index >= len(blocks):
                raise AssertionError("known final model lacks its retained block")
            expected_block = [(-variable if bit(packed, variable) else variable) for variable in range(1, PRIMARY_VARIABLES + 1)]
            if blocks[index] != expected_block or any(literal_true(packed, literal) for literal in blocks[index]):
                raise AssertionError("block polarity does not exactly reject its source primary vector")

        audited.append({
            "round": round_number,
            "primary_vector_sha256": primary_hash,
            "prior_blocks_satisfied": index,
            "base_clauses_satisfied": BASE_CLAUSES,
            "boundary_hamming_distance": distance,
            "fixed_induced_order_30_equal": fixed_equal,
            "graph_clique_number": omega,
            "complement_clique_number": alpha,
            "destroy_core_neighborhood_rows_distinct": rows_distinct,
            "destroy_permutation_normal_form_sha256": destroy_normal_form,
            "supplied_target": target_label,
            "networkx_target_isomorphism": target is not None,
        })

    first_falsifies_own: bool | None = None
    second_satisfies_first: bool | None = None
    if blocks:
        # Mutation sentinels for the independent block evaluator.
        first = (artifact_dir / "model-001.bits").read_bytes()
        first_falsifies_own = not any(literal_true(first, literal) for literal in blocks[0])
        if not first_falsifies_own:
            raise AssertionError("first-block mutation sentinel failed")
        if len(models) > 1:
            second = (artifact_dir / "model-002.bits").read_bytes()
            second_satisfies_first = any(literal_true(second, literal) for literal in blocks[0])
            if not second_satisfies_first:
                raise AssertionError("second-model prior-block sentinel failed")

    payload = {
        "schema_version": 1,
        "status": "novel42_labelled_cegar_cold_audit_pass",
        "scope": "the retained labelled models, immutable base CNF, and ordered primary blocks only",
        "production_report_sha256": digest(production_path),
        "corpus_sha256": digest(corpus_path),
        "base_logical_sha256": logical_digest(base_path),
        "models_checked": len(models),
        "blocks_checked": len(blocks),
        "distinct_primary_vectors": len(seen_primary),
        "distinct_reached_supplied_classes": len(reached),
        "models_with_distinct_destroy_core_rows": sum(item["destroy_core_neighborhood_rows_distinct"] for item in audited),
        "distinct_destroy_permutation_normal_forms_when_defined": len(destroy_normal_forms),
        "models": audited,
        "mutation_sentinels": {
            "first_model_falsifies_its_own_block": first_falsifies_own,
            "second_model_satisfies_first_block": second_satisfies_first,
        },
        "independent_methods": [
            "independent primary-edge mapping",
            "direct evaluation of every base DIMACS clause and every earlier block",
            "NetworkX graph6 parsing and maximal-clique enumeration in graph and complement",
            "NetworkX isomorphism to each nauty-identified supplied target",
        ],
        "conclusion": (
            f"All {len(models)} retained primary assignments are distinct and satisfy the exact labelled CEGAR scope; "
            "this audit does not turn labelled blocks into class blocks or establish a boundary exclusion."
        ),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"], "models_checked": len(models),
        "distinct_reached_supplied_classes": len(reached),
        "report": str(output), "report_sha256": digest(output),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
