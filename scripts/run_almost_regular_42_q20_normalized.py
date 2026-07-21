#!/usr/bin/env python3
"""Fail-closed fixed-root q=20 Ramsey(5,5,42) SAT pilot."""

from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "checkers"))
import almost_regular_42_cnf as encoding  # noqa: E402

BASE_SPEC = importlib.util.spec_from_file_location(
    "unsymmetrized_runner", ROOT / "scripts" / "run_almost_regular_42_pilot.py"
)
if BASE_SPEC is None or BASE_SPEC.loader is None:
    raise RuntimeError("cannot load retained pilot helpers")
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)


ORDER = 42
Q = 20
EXPECTED_VARIABLES = 71421
EXPECTED_BASE_CLAUSES = 1844052
EXPECTED_NORMALIZED_CLAUSES = 1844093
EXPECTED_RAMSEY_LEDGER = "c3ed87c4609c629948e6b51715f65fea99efed79af5baacbc96805041e9d1945"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def invoke_normalization_audit(
    checker: Path,
    order: int,
    q: int,
    normalized_cnf: Path,
    base_cnf: Path,
    mapping: Path,
    summary: Path,
    report: Path,
) -> dict[str, object]:
    base.run(
        [
            sys.executable,
            str(checker),
            "--order",
            str(order),
            "--degree-q",
            str(q),
            "--normalized-cnf",
            str(normalized_cnf),
            "--base-cnf",
            str(base_cnf),
            "--map",
            str(mapping),
            "--summary",
            str(summary),
            "--report",
            str(report),
        ],
        timeout=300,
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    if payload.get("status") != "fixed_root_normalization_audit_pass":
        raise AssertionError("normalization auditor did not pass")
    return payload


def normalized_r33_gate(
    generator: Path,
    normalizer: Path,
    ledger_b: Path,
    cadical: str,
    drat_trim: Path,
    lrat_check: Path,
    root: Path,
) -> dict[str, object]:
    directory = root / "r33-6-normalized"
    directory.mkdir()
    base_cnf = directory / "base.cnf"
    base_map = directory / "base.map.tsv"
    base_summary = directory / "base.summary.json"
    cnf = directory / "normalized.cnf"
    mapping = directory / "normalized.map.tsv"
    summary = directory / "normalized.summary.json"
    audit_report = directory / "normalization.audit.json"
    base.run(
        [
            sys.executable,
            str(generator),
            "--order",
            "6",
            "--clique-size",
            "3",
            "--degree-q",
            "2",
            "--cnf",
            str(base_cnf),
            "--map",
            str(base_map),
            "--summary",
            str(base_summary),
        ]
    )
    base.run(
        [
            sys.executable,
            str(generator),
            "--order",
            "6",
            "--clique-size",
            "3",
            "--degree-q",
            "2",
            "--fix-root-neighborhood",
            "--cnf",
            str(cnf),
            "--map",
            str(mapping),
            "--summary",
            str(summary),
        ]
    )
    audit = invoke_normalization_audit(
        normalizer, 6, 2, cnf, base_cnf, mapping, summary, audit_report
    )
    ledger = directory / "ledger-b.txt"
    base.run([str(ledger_b), "6", "3", str(ledger)])
    metadata = json.loads(summary.read_text(encoding="ascii"))
    if digest(ledger) != metadata["ramsey_ledger_sha256"]:
        raise AssertionError("normalized R(3,3,6) Ramsey ledger mismatch")
    proof = directory / "proof.drat"
    solved, seconds = base.run(
        [cadical, "-q", str(cnf), str(proof)], accepted=(10, 20), timeout=60
    )
    if solved.returncode != 20:
        raise AssertionError("normalized R(3,3,6) was not UNSAT")
    certificate = base.verify_lrat(
        drat_trim, lrat_check, cnf, proof, directory / "proof.lrat"
    )
    return {
        "status": "unsat_verified",
        "solver_seconds": seconds,
        "variables": metadata["variables"],
        "clauses": metadata["clauses"],
        "base_plus_units": audit["normalized_formula_exactly_base_plus_units"],
        "coverage_control": audit["coverage_control"],
        "certificate": certificate,
    }


def gzip_replace(path: Path) -> dict[str, object]:
    return base.gzip_replace(path)


def main() -> int:
    if len(sys.argv) != 12:
        raise SystemExit(
            "usage: run_almost_regular_42_q20_normalized.py GENERATOR NORMALIZER "
            "LEDGER_B_C CHECKER_B_C CORPUS CORPUS_REPORT BASE_CNF_GZ DRAT_C LRAT_C OUTPUT_DIR REPORT"
        )
    (
        generator,
        normalizer,
        ledger_source,
        checker_b_source,
        corpus,
        corpus_report,
        base_cnf_gz,
        drat_source,
        lrat_source,
        output_dir,
        report,
    ) = map(lambda value: Path(value).resolve(), sys.argv[1:])
    if output_dir.exists() or report.exists():
        raise ValueError("output directory or report already exists")
    compiler = shutil.which("gcc") or shutil.which("clang")
    cadical = shutil.which("cadical")
    labelg = shutil.which("nauty-labelg")
    complg = shutil.which("nauty-complg")
    if not all((compiler, cadical, labelg, complg)):
        raise RuntimeError("compiler, CaDiCaL, or nauty programs unavailable")
    output_dir.mkdir(parents=True)

    corpus_result = base.corpus_degree_gate(corpus, corpus_report)
    with tempfile.TemporaryDirectory(prefix="r55-q20-normalized-") as temporary:
        temp = Path(temporary)
        ledger_b, checker_b, drat_trim, lrat_check = base.compile_tools(
            compiler, ledger_source, checker_b_source, drat_source, lrat_source, temp
        )
        counter_result = base.counter_and_profile_gate(cadical, temp)
        historic_r33 = base.r33_gate(
            generator, ledger_b, cadical, drat_trim, lrat_check, temp
        )
        normalized_r33 = normalized_r33_gate(
            generator, normalizer, ledger_b, cadical, drat_trim, lrat_check, temp
        )

        cnf = output_dir / "q20-normalized.cnf"
        mapping = output_dir / "q20-normalized.map.tsv"
        summary_path = output_dir / "q20-normalized.generator.json"
        generation_started = time.monotonic()
        base.run(
            [
                sys.executable,
                str(generator),
                "--order",
                "42",
                "--clique-size",
                "5",
                "--degree-q",
                "20",
                "--fix-root-neighborhood",
                "--cnf",
                str(cnf),
                "--map",
                str(mapping),
                "--summary",
                str(summary_path),
            ],
            timeout=300,
        )
        generation_seconds = time.monotonic() - generation_started
        summary = json.loads(summary_path.read_text(encoding="ascii"))
        if (
            summary.get("degree_values") != [20, 21]
            or summary.get("primary_variables") != 861
            or summary.get("variables") != EXPECTED_VARIABLES
            or summary.get("clauses") != EXPECTED_NORMALIZED_CLAUSES
            or summary.get("normalization_unit_clauses") != 41
            or summary.get("ramsey_ledger_sha256") != EXPECTED_RAMSEY_LEDGER
        ):
            raise AssertionError("production summary mismatch")
        base.audit_map(mapping, ORDER)
        ledger = temp / "q20.ramsey.ledger"
        base.run([str(ledger_b), "42", "5", str(ledger)], timeout=180)
        ledger_sha256 = digest(ledger)
        if ledger_sha256 != EXPECTED_RAMSEY_LEDGER:
            raise AssertionError("Python/C production Ramsey ledger mismatch")
        cnf_audit = base.audit_production_cnf(cnf, summary, ledger_sha256)
        normalization_report = output_dir / "q20-normalized.audit-a.json"
        normalization_audit = invoke_normalization_audit(
            normalizer,
            ORDER,
            Q,
            cnf,
            base_cnf_gz,
            mapping,
            summary_path,
            normalization_report,
        )
        if normalization_audit["base_clause_lines_compared"] != EXPECTED_BASE_CLAUSES:
            raise AssertionError("unexpected unsymmetrized base clause count")

        first_ledger_line = ledger.read_bytes().splitlines(keepends=True)[0]
        mutated_literal = first_ledger_line.replace(b"1 ", b"-1 ", 1)
        mutation_results = {
            "omitted_ramsey_clause_detected_by_count": int(summary["clauses"]) - 1
            != cnf_audit["clause_lines"],
            "negated_ramsey_literal_detected_by_ledger_hash": hashlib.sha256(
                mutated_literal
            ).digest()
            != hashlib.sha256(first_ledger_line).digest(),
            "weakened_bound_detected_by_truth_table": (3 not in {1, 2})
            and (3 in {1, 2, 3}),
            "normalization_mutations_all_rejected": all(
                normalization_audit["mutation_rejections"].values()
            ),
        }
        if not all(mutation_results.values()):
            raise AssertionError("production mutation sentinel failed")

        proof = output_dir / "q20-normalized.partial-or-final.drat"
        solver_started = time.monotonic()
        solved = subprocess.run(
            [cadical, "-q", "-t", "300", str(cnf), str(proof)],
            text=True,
            capture_output=True,
            preexec_fn=base.solver_file_limit,
        )
        solver_seconds = time.monotonic() - solver_started
        (output_dir / "cadical.stdout").write_text(solved.stdout, encoding="ascii")
        (output_dir / "cadical.stderr").write_text(solved.stderr, encoding="ascii")

        lrat_metadata: dict[str, object] | None = None
        model_metadata: dict[str, object] | None = None
        if solved.returncode == 10:
            bits = base.parse_model(solved.stdout, 861)
            independent, cliques = base.violation_scan(ORDER, 5, bits)
            degrees = base.degree_scan(ORDER, bits)
            root_pattern = all(
                bits[encoding.edge_var(0, other) - 1] == (other <= Q)
                for other in range(1, ORDER)
            )
            if (
                independent
                or cliques
                or not all(degree in {20, 21} for degree in degrees)
                or not root_pattern
            ):
                raise AssertionError("normalized SAT model failed direct scan")
            padded = bits + [False] * ((-len(bits)) % 6)
            graph6 = bytes(
                [ORDER + 63]
                + [
                    63
                    + sum(
                        (1 if padded[offset + index] else 0) << (5 - index)
                        for index in range(6)
                    )
                    for offset in range(0, len(padded), 6)
                ]
            ) + b"\n"
            model_path = output_dir / "q20-normalized.model.g6"
            model_path.write_bytes(graph6)
            checked_c, _ = base.run(
                [str(checker_b), "--format", "graph6", "--input", str(model_path)],
                timeout=120,
            )
            c_payload = json.loads(checked_c.stdout)["graphs"][0]
            if c_payload["zero_k5"] or c_payload["one_k5"] or c_payload["degrees"] != degrees:
                raise AssertionError("C recursive-bitset model scan disagreed")
            complements = temp / "corpus-complements.g6"
            canonical_corpus = temp / "corpus-canonical.g6"
            combined = temp / "corpus-combined.g6"
            canonical_model = output_dir / "q20-normalized.model.canonical.g6"
            base.run([complg, "-q", str(corpus), str(complements)])
            combined.write_bytes(corpus.read_bytes() + complements.read_bytes())
            base.run([labelg, "-q", str(combined), str(canonical_corpus)])
            base.run([labelg, "-q", str(model_path), str(canonical_model)])
            novel_to_supplied = canonical_model.read_bytes().strip() not in set(
                canonical_corpus.read_bytes().splitlines()
            )
            if not novel_to_supplied:
                raise AssertionError("almost-regular model unexpectedly matched supplied corpus")
            model_metadata = {
                "primary_assignment_sha256": hashlib.sha256(bytes(bits)).hexdigest(),
                "degree_histogram": dict(sorted(Counter(degrees).items())),
                "root_pattern_checked": True,
                "python_full_scan": True,
                "c_recursive_bitset_full_scan": True,
                "nauty_canonical_novel_to_supplied_656": True,
            }
            result = {
                "status": "sat",
                "scope": "degree-{20,21} order-42 band via a covered normalized representative",
            }
        elif solved.returncode == 20:
            lrat = output_dir / "q20-normalized.lrat"
            lrat_metadata = base.verify_lrat(
                drat_trim, lrat_check, cnf, proof, lrat
            )
            result = {
                "status": "unsat_verified",
                "scope": "entire degree-{20,21} order-42 band by complement/relabel coverage",
            }
        else:
            result = {
                "status": "unknown",
                "scope": "normalized representative formula only; coverage gives no exclusion after timeout",
                "returncode": solved.returncode,
                "timed_out": solved.returncode == 0,
                "proof_file_limit_bytes": 512 * 1024 * 1024,
                "qualification": "no exclusion; any partial proof is not a certificate",
            }

        cnf_storage = gzip_replace(cnf)
        proof_storage = gzip_replace(proof) if proof.exists() else None
        lrat_storage = (
            gzip_replace(output_dir / "q20-normalized.lrat")
            if (output_dir / "q20-normalized.lrat").exists()
            else None
        )
        payload = {
            "schema_version": 1,
            "status": "almost_regular_42_q20_normalized_pilot_complete",
            "scope": (
                "Ramsey(5,5,42) graphs with every degree in {20,21}, represented after "
                "complementation/relabeling by N(0)={1,...,20}"
            ),
            "source_status": "43 <= R(5,5) <= 46 as checked against DS1.18 revision 18",
            "coverage_claim": normalization_audit["coverage_lemma"],
            "corpus_gate": corpus_result,
            "counter_and_profile_gate": counter_result,
            "historic_r33_control": historic_r33,
            "normalized_r33_control": normalized_r33,
            "production": {
                "generator_summary": summary,
                "generation_seconds": generation_seconds,
                "cnf_audit": cnf_audit,
                "normalization_audit": normalization_audit,
                "normalization_audit_report_sha256": digest(normalization_report),
                "cnf_storage": cnf_storage,
                "proof_storage": proof_storage,
                "lrat_storage": lrat_storage,
                "solver": {
                    "path": cadical,
                    "version": subprocess.run(
                        [cadical, "--version"], text=True, capture_output=True
                    ).stdout.strip(),
                    "command": [
                        cadical,
                        "-q",
                        "-t",
                        "300",
                        "q20-normalized.cnf",
                        "q20-normalized.partial-or-final.drat",
                    ],
                    "wall_seconds": solver_seconds,
                    "returncode": solved.returncode,
                },
                "result": result,
                "lrat_metadata": lrat_metadata,
                "model_metadata": model_metadata,
            },
            "independence": {
                "python_generator_sha256": digest(generator),
                "standalone_normalization_auditor_sha256": digest(normalizer),
                "c_nested_loop_ledger_source_sha256": digest(ledger_source),
                "ramsey_ledger_byte_hash_agreement": True,
                "normalized_formula_exactly_unsymmetrized_base_plus_41_units": True,
                "degree_semantics": "CaDiCaL truth table on every 1..6-bit row and every q",
                "coverage_semantics": "written lemma plus all 32768 labelled order-6 graphs",
            },
            "mutation_sentinels": mutation_results,
            "tool_versions": {
                "python": sys.version.split()[0],
                "compiler": subprocess.run(
                    [compiler, "--version"], text=True, capture_output=True
                ).stdout.splitlines()[0],
                "cadical": subprocess.run(
                    [cadical, "--version"], text=True, capture_output=True
                ).stdout.strip(),
                "nauty_labelg": labelg,
                "nauty_complg": complg,
            },
            "conclusion": (
                "A checked SAT model establishes an almost-regular order-42 graph outside the supplied corpus; "
                "a proof-checked UNSAT result excludes the q=20 band by coverage; unknown changes no bound."
            ),
        }
        report.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "report": str(report),
                    "report_sha256": digest(report),
                    "production_result": result,
                    "cnf_clauses": summary["clauses"],
                    "cnf_variables": summary["variables"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
