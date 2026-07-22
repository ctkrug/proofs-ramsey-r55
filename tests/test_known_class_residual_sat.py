from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import networkx as nx


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load("residual_sat_producer", "scripts/run_known_class_residual_sat.py")
auditor = load("residual_sat_auditor", "checkers/known_class_residual_sat_audit.py")


class ResidualSatTests(unittest.TestCase):
    def test_immutable_attempt_allocation_preserves_interrupted_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            root = Path(temporary_name)
            requested_output = root / "output"
            requested_report = root / "report.json"
            first_output, first_report, first_index = producer.allocate_attempt_paths(
                requested_output, requested_report
            )
            (first_output / "partial-proof").write_text("preserve me", encoding="utf-8")
            second_output, second_report, second_index = producer.allocate_attempt_paths(
                requested_output, requested_report
            )
            self.assertEqual((first_output, first_report, first_index), (requested_output, requested_report, 0))
            self.assertEqual(second_index, 1)
            self.assertEqual(second_output.name, "output.attempt-0001")
            self.assertEqual(second_report.name, "report.attempt-0001.json")
            self.assertEqual((first_output / "partial-proof").read_text(encoding="utf-8"), "preserve me")

    def test_cold_tied_expansion_is_exact_and_duplicate_free(self) -> None:
        source = nx.Graph()
        source.add_nodes_from(range(auditor.N))
        # Exactly one two-vertex tie and ten distinct later rows.
        row_values = [0, 0, *range(1, 11)]
        for vertex, value in zip(auditor.REMOVED, row_values, strict=True):
            for position, core in enumerate(auditor.CORE):
                if value & (1 << position):
                    source.add_edge(vertex, core)
        group_sizes, orders, vectors = auditor.independently_expand_embedding(
            source, tuple(auditor.CORE)
        )
        expected = 1
        import math
        for size in group_sizes:
            expected *= math.factorial(size)
        self.assertEqual(len(orders), expected)
        self.assertEqual(expected, 2)
        self.assertEqual(len({tuple(order) for order in orders}), expected)
        self.assertEqual(len(vectors), expected)

        embedding = tuple(auditor.CORE)
        unique_vectors = sorted(set(vectors))
        entry = {
            "map_pattern_to_host": list(embedding),
            "tie_group_sizes": group_sizes,
            "tie_multiplicity": len(orders),
            "residual_orders": orders,
            "vectors": vectors,
        }
        row = {
            "embedding_count": 1,
            "mapping_stream_sha256": auditor.line_hash([",".join(map(str, embedding))]),
            "vector_occurrences": len(orders),
            "unique_vector_count": len(unique_vectors),
            "vector_stream_sha256": auditor.line_hash(unique_vectors),
        }
        first = {"embeddings": [entry], "unique_vectors": unique_vectors}
        with mock.patch.object(auditor, "independently_enumerate_embeddings", return_value=[embedding]):
            auditor.verify_complete_host_coverage(source, source, first, row, 0)
            entry["residual_orders"] = [orders[0], orders[0]]
            with self.assertRaisesRegex(AssertionError, "exact tied-row expansion"):
                auditor.verify_complete_host_coverage(source, source, first, row, 0)

    def test_proof_checker_timeout_is_incomplete_and_preserves_log(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            root = Path(temporary_name)
            checker = root / "slow-checker"
            checker.write_text("#!/bin/sh\nexec sleep 2\n", encoding="utf-8")
            checker.chmod(0o755)
            cnf, proof = root / "input.cnf", root / "proof.drat"
            cnf.write_text("p cnf 1 1\n1 0\n", encoding="ascii")
            proof.write_bytes(b"")
            for module, name in ((producer, "producer"), (auditor, "auditor")):
                log = root / f"{name}.log"
                checked, _seconds, timed_out = module.run_drat_check(
                    checker, cnf, proof, log, timeout_seconds=0.02
                )
                self.assertIsNone(checked)
                self.assertTrue(timed_out)
                self.assertIn("incomplete", log.read_text(encoding="utf-8"))

    def test_sat_status_distinguishes_known_and_candidate(self) -> None:
        self.assertEqual(producer.sat_status(False), "sat_known_control")
        self.assertEqual(producer.sat_status(True), "sat_corpus_novel_candidate")
        self.assertEqual(auditor.sat_status(False), "sat_known_control")
        self.assertEqual(auditor.sat_status(True), "sat_corpus_novel_candidate")

    def test_vector_block_has_exact_single_assignment_polarity(self) -> None:
        vector = "01" * 213
        clause = producer.vector_block(vector)
        self.assertEqual(len(clause), 426)
        values = {index: vector[index - 1] == "1" for index in range(1, 427)}
        self.assertFalse(producer.clause_true(clause, values))
        values[17] = not values[17]
        self.assertTrue(producer.clause_true(clause, values))
        self.assertEqual(clause, auditor.vector_clause(vector))

    def test_independent_lex_comparator_matches_and_has_unique_auxiliaries(self) -> None:
        left = list(range(1, 31))
        right = list(range(31, 61))
        auxiliary = list(range(61, 90))
        produced = producer.lex_leq_clauses(left, right, auxiliary)
        audited = auditor.comparator(left, right, auxiliary)
        self.assertEqual(produced, audited)
        self.assertEqual(len(produced), 174)

        # Exhaust a smaller three-bit producer gadget and check its direct meaning.
        for left_value in range(8):
            for right_value in range(8):
                clauses = producer.lex_leq_clauses([1, 2, 3], [4, 5, 6], [7, 8])
                satisfying = 0
                for aux in range(4):
                    values = {
                        **{i + 1: bool(left_value & (1 << (2 - i))) for i in range(3)},
                        **{i + 4: bool(right_value & (1 << (2 - i))) for i in range(3)},
                        7: bool(aux & 1), 8: bool(aux & 2),
                    }
                    satisfying += int(all(producer.clause_true(clause, values) for clause in clauses))
                self.assertEqual(satisfying, int(left_value <= right_value))

    def test_producer_and_auditor_reconstruct_same_real_formula(self) -> None:
        records = (ROOT / "sources/r55_42some.g6").read_bytes().splitlines()
        source_matrix = producer.parse_graph6(records[20])
        source_graph = nx.from_graph6_bytes(records[20])
        produced, _ = producer.build_formula(source_matrix)
        audited, raw_count = auditor.reconstruct(source_graph)
        self.assertEqual(produced, audited)
        source_vector = producer.row_sorted_source_vector(source_matrix)
        self.assertEqual(len(source_vector), 426)
        self.assertFalse(producer.clause_true(producer.vector_block(source_vector), {
            index: bit == "1" for index, bit in enumerate(source_vector, 1)
        }))
        self.assertGreater(raw_count, 0)
        self.assertEqual(len(produced) - raw_count, 1914)

    def test_partial_census_fails_before_vector_use(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_name:
            temporary = Path(temporary_name)
            manifest = temporary / "manifest.jsonl"
            manifest.write_text("", encoding="utf-8")
            validation = temporary / "validation.json"
            validation.write_text(json.dumps({
                "status": "valid", "hosts": 656,
                "manifest_sha256": producer.digest(manifest),
                "original_prefix_manifest_sha256": producer.PREFIX_MANIFEST_SHA256,
                "aggregate_host_gate_schedule": producer.HOST_GATE_SCHEDULE,
            }), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "0..655"):
                producer.load_validated_vectors(manifest, validation)
            with self.assertRaisesRegex(AssertionError, "656 manifest rows"):
                auditor.census_vectors(manifest, validation)


if __name__ == "__main__":
    unittest.main()
