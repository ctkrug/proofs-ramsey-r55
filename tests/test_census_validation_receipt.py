from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "receipt_builder", ROOT / "scripts" / "build_known_class_census_validation_receipt.py",
)
assert SPEC and SPEC.loader
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class CensusValidationReceiptTests(unittest.TestCase):
    def test_archived_completed_jobs_build_complete_receipt(self) -> None:
        receipt = BUILDER.build(
            ROOT,
            ROOT / "records" / "labs" / "lab-ramsey-r55-868014a68d6e-completed-awaiting-review-segment-401.json",
            ROOT / "records" / "labs" / "lab-ramsey-r55-8ea9f8eeb6cc-completed-awaiting-review-segment-01.json",
        )
        self.assertEqual(receipt["job_id"], "lab-ramsey-r55-868014a68d6e")
        self.assertEqual(receipt["validation_job_id"], "lab-ramsey-r55-8ea9f8eeb6cc")
        self.assertEqual(len(receipt["checked_artifacts"]), 660)
        self.assertEqual(receipt["checker_exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
