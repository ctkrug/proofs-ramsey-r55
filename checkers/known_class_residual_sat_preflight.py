#!/usr/bin/env python3
"""Fail-closed preflight for the record-21 known-class residual SAT run.

This is not a solver and proves no Ramsey claim.  It compares the production
and cold-audit formula reconstructions, checks the complete census block union,
and executes three corruption sentinels before a long solve is submitted.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import networkx as nx


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load_module("known_class_residual_sat_producer", "scripts/run_known_class_residual_sat.py")
auditor = load_module("known_class_residual_sat_auditor", "checkers/known_class_residual_sat_audit.py")


def sha256(path: Path) -> str:
    state = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            state.update(chunk)
    return state.hexdigest()


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: known_class_residual_sat_preflight.py MANIFEST VALIDATION CORPUS OUTPUT"
        )
    manifest, validation, corpus, output = map(Path, sys.argv[1:])
    if output.exists():
        raise ValueError("preflight output already exists")
    if sha256(corpus) != producer.CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")

    vectors, counts = producer.load_validated_vectors(manifest, validation)
    cold_vectors, cold_occurrences = auditor.census_vectors(manifest, validation)
    if vectors != cold_vectors or counts["vector_occurrences"] != cold_occurrences:
        raise AssertionError("producer and cold parser disagree on the census union")

    records = corpus.read_bytes().splitlines()
    source_matrix = producer.parse_graph6(records[producer.SOURCE_RECORD - 1])
    source_graph = nx.from_graph6_bytes(records[auditor.CORE_SOURCE - 1])
    produced, _row_pairs = producer.build_formula(source_matrix)
    independently_reconstructed, raw_count = auditor.reconstruct(source_graph)
    if produced != independently_reconstructed:
        raise AssertionError("producer and cold auditor reconstruct different base formulas")
    source_vector = producer.row_sorted_source_vector(source_matrix)
    if source_vector not in vectors:
        raise AssertionError("record-21 positive-control vector is not blocked")
    source_values = {
        variable: bit == "1" for variable, bit in enumerate(source_vector, 1)
    }
    if not all(
        producer.clause_true(clause, source_values)
        for clause in produced
        if all(abs(literal) <= producer.PRIMARY_VARIABLES for literal in clause)
    ):
        raise AssertionError("record-21 control violates a primary-only base clause")
    if producer.clause_true(producer.vector_block(source_vector), source_values):
        raise AssertionError("the exact source-control block does not reject its assignment")

    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
    positive_index = next(index for index, row in enumerate(rows) if row["unique_vector_count"])
    artifact = Path(rows[positive_index]["artifact"])
    if not artifact.is_absolute():
        artifact = manifest.parent / artifact
    with gzip.open(artifact, "rt", encoding="utf-8") as handle:
        packet = json.load(handle)
    original_host_vectors = packet["bitset"]["unique_vectors"]
    mutated_host_vectors = list(original_host_vectors)
    first = mutated_host_vectors[0]
    mutated_host_vectors[0] = ("1" if first[0] == "0" else "0") + first[1:]
    vector_bit_flip_rejected = (
        auditor.line_hash(mutated_host_vectors) != rows[positive_index]["vector_stream_sha256"]
    )

    with tempfile.TemporaryDirectory(prefix="r55-residual-preflight-") as temporary_name:
        mutated_validation = Path(temporary_name) / "validation.json"
        validation_payload = json.loads(validation.read_text(encoding="utf-8"))
        validation_payload["manifest_sha256"] = "0" * 64
        mutated_validation.write_text(
            json.dumps(validation_payload, sort_keys=True) + "\n", encoding="utf-8"
        )
        manifest_hash_mutation_rejected = False
        try:
            producer.load_validated_vectors(manifest, mutated_validation)
        except AssertionError:
            manifest_hash_mutation_rejected = True

    expected_formula = produced + [auditor.vector_clause(vector) for vector in vectors]
    mutated_formula = list(expected_formula)
    changed_block = list(mutated_formula[-1])
    changed_block[0] = -changed_block[0]
    mutated_formula[-1] = tuple(changed_block)
    block_clause_mutation_rejected = mutated_formula != expected_formula

    mutations = {
        "vector_bit_flip_rejected_by_stream_hash": vector_bit_flip_rejected,
        "manifest_hash_alteration_rejected_before_vector_use": manifest_hash_mutation_rejected,
        "block_literal_replacement_rejected_by_independent_formula_comparison": block_clause_mutation_rejected,
    }
    if not all(mutations.values()):
        raise AssertionError(f"preflight mutation sentinel failed: {mutations}")

    payload = {
        "schema_version": 1,
        "status": "known_class_residual_sat_preflight_pass",
        "scope": "record-21 frozen order-30 core and validated supplied-656-class block union only",
        "inputs": {
            "manifest": {"path": str(manifest), "sha256": sha256(manifest)},
            "validation": {"path": str(validation), "sha256": sha256(validation)},
            "corpus": {"path": str(corpus), "sha256": sha256(corpus)},
            "producer": {
                "path": str(ROOT / "scripts/run_known_class_residual_sat.py"),
                "sha256": sha256(ROOT / "scripts/run_known_class_residual_sat.py"),
            },
            "cold_auditor": {
                "path": str(ROOT / "checkers/known_class_residual_sat_audit.py"),
                "sha256": sha256(ROOT / "checkers/known_class_residual_sat_audit.py"),
            },
        },
        "census": {
            "hosts": counts["hosts"],
            "vector_occurrences": counts["vector_occurrences"],
            "unique_vectors": len(vectors),
            "all_vectors_426_bit_binary": all(
                len(vector) == producer.PRIMARY_VARIABLES
                and not (set(vector) - {"0", "1"})
                for vector in vectors
            ),
            "record_21_control_vector_present": True,
        },
        "formula": {
            "raw_ramsey_clauses": raw_count,
            "lex_clauses": len(produced) - raw_count,
            "base_clauses": len(produced),
            "class_blocks": len(vectors),
            "total_clauses": len(expected_formula),
            "primary_variables": producer.PRIMARY_VARIABLES,
            "total_variables": producer.TOTAL_VARIABLES,
            "producer_cold_reconstruction_byte_equal": True,
        },
        "mutations": mutations,
        "claim_limit": "preflight only; no SAT/UNSAT or Ramsey conclusion",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(output), "sha256": sha256(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
