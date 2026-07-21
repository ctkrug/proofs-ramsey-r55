#!/usr/bin/env python3
"""Fail-closed exact gate for the 43-bit distance-six slice of the R55 seed."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import run_publisher_radius1_gate as radius1
from z3 import get_version_string


ORDER = 43
EXPECTED_NORMAL_FORM = {
    "positive_pair_shapes": [[0, 18], [0, 20]],
    "negative_triple_shapes": [[0, 5, 24]],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(command: list[str]) -> tuple[dict[str, object], float]:
    started = time.monotonic()
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    elapsed = time.monotonic() - started
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout), elapsed


def expect_rejection(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode == 0:
        raise AssertionError(f"malformed input was accepted: {command}")
    lines = result.stderr.strip().splitlines()
    return lines[-1] if lines else f"exit {result.returncode}"


def cyclic_orbit_profile(matrix: list[list[int]]) -> list[dict[str, object]]:
    profile = []
    for distance in range(1, 22):
        word = [matrix[u][(u + distance) % ORDER] for u in range(ORDER)]
        profile.append({
            "distance": distance,
            "ones": sum(word),
            "cyclic_transitions": sum(word[index] != word[(index + 1) % ORDER] for index in range(ORDER)),
            "word_u_order": "".join(map(str, word)),
        })
    return profile


def transformed_word(word: str) -> str:
    return "".join(word[(27 * index) % ORDER] for index in range(ORDER))


def interval_class(word: str) -> str | None:
    transformed = transformed_word(word)
    transitions = sum(transformed[index] != transformed[(index + 1) % ORDER] for index in range(ORDER))
    if transitions == 2 and transformed.count("1") in (24, 25):
        return f"step27_cyclic_interval_length_{transformed.count('1')}"
    return None


def interval_word(length: int, start: int = 0) -> str:
    bits = ["0"] * ORDER
    for offset in range(length):
        bits[(27 * (start + offset)) % ORDER] = "1"
    return "".join(bits)


def reduced_burden(word: str, positive_pairs: list[list[int]], negative_triples: list[list[int]]) -> int:
    bits = [bit == "1" for bit in word]
    zero_conflicts = 2 * sum(not any(bits[index] for index in pair) for pair in positive_pairs)
    one_conflicts = sum(all(bits[index] for index in triple) for triple in negative_triples)
    return zero_conflicts + one_conflicts


def matrix_with_word(base: list[list[int]], word: str) -> list[list[int]]:
    matrix = [row[:] for row in base]
    for u, bit in enumerate(word):
        v = (u + 6) % ORDER
        matrix[u][v] = matrix[v][u] = int(bit)
    return matrix


def main() -> int:
    if len(sys.argv) != 9:
        raise SystemExit(
            "usage: run_distance6_slice_gate.py SLICE_A SLICE_B_C RADIUS1_A RADIUS1_B_C "
            "BODY1 BODY2 RADIUS2_REPORT OUTPUT"
        )
    slice_a = Path(sys.argv[1]).resolve()
    slice_b_source = Path(sys.argv[2]).resolve()
    radius1_a = Path(sys.argv[3]).resolve()
    radius1_b_source = Path(sys.argv[4]).resolve()
    body1 = Path(sys.argv[5]).resolve()
    body2 = Path(sys.argv[6]).resolve()
    radius2_report_path = Path(sys.argv[7]).resolve()
    output = Path(sys.argv[8]).resolve()
    root = Path.cwd().resolve()

    frozen_bodies = [(root / descriptor["body"]).resolve() for descriptor in radius1.RETRIEVALS]
    if [body1, body2] != frozen_bodies:
        raise ValueError("body arguments are not the two frozen retrieval paths")
    retrievals = [radius1.validate_retrieval(root, descriptor) for descriptor in radius1.RETRIEVALS]
    if body1.read_bytes() != body2.read_bytes():
        raise AssertionError("the two publisher retrieval bodies differ")
    radius2_report = json.loads(radius2_report_path.read_text(encoding="utf-8"))
    if radius2_report.get("status") != "publisher_seed_radius2_pass":
        raise ValueError("the complete radius-two gate is not admitted")
    if radius2_report.get("source", {}).get("body_sha256") != radius1.BODY_SHA256:
        raise ValueError("radius-two report is linked to a different source body")

    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise RuntimeError("a C compiler is required")
    with tempfile.TemporaryDirectory(prefix="r55-distance6-slice-") as temporary:
        temp = Path(temporary)
        slice_b = temp / "distance6_slice_b"
        radius1_b = temp / "publisher_radius1_b"
        compile_slice = [
            compiler, "-std=c11", "-O3", "-Wall", "-Wextra", "-Werror",
            str(slice_b_source), "-o", str(slice_b),
        ]
        compile_radius1 = [
            compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
            str(radius1_b_source), "-o", str(radius1_b),
        ]
        subprocess.run(compile_slice, check=True)
        subprocess.run(compile_radius1, check=True)

        payload_a, elapsed_a = run_json([sys.executable, str(slice_a), str(body1)])
        payload_b, elapsed_b = run_json([str(slice_b), str(body1)])
        scalar_fields = (
            "order", "raw_active_five_sets", "unique_constraints",
            "positive_pair_multiplicity", "negative_triple_multiplicity",
            "burden_at_most", "minimum_burden", "minimum_model_count",
        )
        if any(payload_a[field] != payload_b[field] for field in scalar_fields):
            raise AssertionError("independent slice checkers disagree on a scalar result")
        positive_a = sorted(payload_a["positive_pairs"])
        positive_b = sorted(payload_b["positive_pairs"])
        negative_a = sorted(payload_a["negative_triples"])
        negative_b = sorted(payload_b["negative_triples"])
        words_a = sorted(payload_a["minimum_words_u_order"])
        words_b = sorted(payload_b["minimum_words_u_order"])
        if positive_a != positive_b or negative_a != negative_b:
            raise AssertionError("independent reduced constraint families disagree")
        if words_a != words_b:
            raise AssertionError("independent complete optimum model sets disagree")
        if payload_a["normal_form"] != EXPECTED_NORMAL_FORM:
            raise AssertionError("reduced cyclic normal form mismatch")
        if payload_a["burden_at_most"] != {"0": "unsat", "1": "unsat", "2": "sat"}:
            raise AssertionError("slice burden bounds mismatch")

        classifications = Counter(interval_class(word) for word in words_a)
        if None in classifications or classifications != Counter({
            "step27_cyclic_interval_length_24": 43,
            "step27_cyclic_interval_length_25": 43,
        }):
            raise AssertionError("complete optimum classification mismatch")
        if payload_a["minimum_model_classification"] != dict(sorted(classifications.items())):
            raise AssertionError("checker A classification does not match the gate")

        base = radius1.matrix_from_raw(body1.read_bytes())
        profile = cyclic_orbit_profile(base)
        exceptional = [item for item in profile if item["ones"] not in (0, ORDER)]
        if len(exceptional) != 1 or exceptional[0]["distance"] != 6 or exceptional[0]["ones"] != 24:
            raise AssertionError("publisher seed is not the expected one-orbit defect")
        seed_word = exceptional[0]["word_u_order"]
        if interval_class(seed_word) != "step27_cyclic_interval_length_24" or seed_word not in words_a:
            raise AssertionError("publisher distance-six word is not an enumerated length-24 optimum")

        controls = {
            "publisher_seed": seed_word,
            "length24_rotation": interval_word(24, 7),
            "length25_optimum": interval_word(25, 0),
            "length25_rotation": interval_word(25, 11),
            "length23_nonoptimum": interval_word(23, 0),
            "length26_nonoptimum": interval_word(26, 0),
        }
        direct_rescans: dict[str, object] = {}
        for name, word in controls.items():
            matrix = matrix_with_word(base, word)
            path = temp / f"{name}.txt"
            path.write_bytes(radius1.raw_matrix_bytes(matrix))
            result_a, _ = run_json([sys.executable, str(radius1_a), "--input", str(path), "--seed-only"])
            result_b, _ = run_json([str(radius1_b), "--input", str(path), "--seed-only"])
            identity_a = {
                "zero_k5": sorted(result_a["seed"]["zero_k5"]),
                "one_k5": sorted(result_a["seed"]["one_k5"]),
            }
            identity_b = {
                "zero_k5": sorted(result_b["seed"]["zero_k5"]),
                "one_k5": sorted(result_b["seed"]["one_k5"]),
            }
            expected = reduced_burden(word, positive_a, negative_a)
            observed = len(identity_a["zero_k5"]) + len(identity_a["one_k5"])
            if identity_a != identity_b or observed != expected:
                raise AssertionError(f"full K5 rescan disagrees with reduced burden for {name}")
            direct_rescans[name] = {
                "word_u_order": word,
                "step27_word": transformed_word(word),
                "reduced_burden": expected,
                **identity_a,
                "independent_full_k5_identity_agreement": True,
            }

        malformed_bytes: dict[str, bytes] = {}
        changed = bytearray(body1.read_bytes())
        first_zero = changed.find(b"0", changed.find(b"\n") + 1)
        changed[first_zero] = ord("x")
        malformed_bytes["nonbinary"] = bytes(changed)
        asymmetric = [row[:] for row in base]
        asymmetric[0][1] ^= 1
        malformed_bytes["asymmetric"] = radius1.raw_matrix_bytes(asymmetric)
        parser_rejections: dict[str, object] = {}
        for name, raw in malformed_bytes.items():
            path = temp / f"malformed-{name}.txt"
            path.write_bytes(raw)
            parser_rejections[name] = {
                "checker_a": expect_rejection([sys.executable, str(slice_a), str(path)]),
                "checker_b": expect_rejection([str(slice_b), str(path)]),
            }

        report = {
            "schema_version": 1,
            "status": "distance6_slice_exact_pass",
            "claim_scope": (
                "all 2^43 assignments to the cyclic-distance-6 edge orbit of the frozen Springer K43 "
                "seed, with the other 20 cyclic-distance orbits fixed; not the full 903-edge space, a "
                "Ramsey witness, a global optimum, or a changed Ramsey bound"
            ),
            "source": {
                "authority": "Springer publisher-controlled static-content URL",
                "url": radius1.URL,
                "body_sha256": radius1.BODY_SHA256,
                "body_bytes": radius1.BODY_BYTES,
                "dual_retrieval_byte_identity": True,
                "retrievals": retrievals,
            },
            "upstream_radius2_gate": {
                "path": str(radius2_report_path),
                "sha256": digest(radius2_report_path),
                "status": radius2_report["status"],
            },
            "checker_a": {
                "path": str(slice_a),
                "sha256": digest(slice_a),
                "method": payload_a["checker"],
                "z3_version": get_version_string(),
                "seconds": elapsed_a,
            },
            "checker_b": {
                "path": str(slice_b_source),
                "source_sha256": digest(slice_b_source),
                "compiled_binary_sha256": digest(slice_b),
                "compile_command": compile_slice[:-1] + ["<temporary>/distance6_slice_b"],
                "compiler_version": subprocess.run(
                    [compiler, "--version"], text=True, capture_output=True, check=True
                ).stdout.splitlines()[0],
                "method": payload_b["checker"],
                "seconds": elapsed_b,
            },
            "independence": (
                "Checker A independently derives all active five-sets in Python and asks Z3 for every "
                "assignment of raw burden at most two. Checker B separately derives and deduplicates "
                "the constraints in C, then uses a custom DPLL enumerator over every admissible "
                "zero-, one-, and two-violation relaxation case."
            ),
            "cyclic_orbit_profile": profile,
            "distance6_seed_word": {
                "u_order": seed_word,
                "step27_order": transformed_word(seed_word),
                "ones": seed_word.count("1"),
                "classification": interval_class(seed_word),
            },
            "reduced_constraint_system": {
                "variables": "x_u colors edge {u,u+6 mod 43}",
                "coordinate": payload_a["coordinate"],
                "raw_active_five_sets": payload_a["raw_active_five_sets"],
                "unique_constraints": payload_a["unique_constraints"],
                "positive_pairs": positive_a,
                "positive_pair_multiplicity": payload_a["positive_pair_multiplicity"],
                "negative_triples": negative_a,
                "negative_triple_multiplicity": payload_a["negative_triple_multiplicity"],
                "normal_form": EXPECTED_NORMAL_FORM,
                "interpretation": (
                    "for every t in Z_43, zeros may not occupy both t and t+18 or both t and t+20; "
                    "ones may not occupy all of t, t+5, and t+24"
                ),
            },
            "exact_result": {
                "burden_at_most": payload_a["burden_at_most"],
                "minimum_burden": payload_a["minimum_burden"],
                "minimum_model_count": payload_a["minimum_model_count"],
                "classification": dict(sorted(classifications.items())),
                "minimum_words_u_order": words_a,
                "independent_complete_model_set_agreement": True,
            },
            "direct_full_k5_rescans": direct_rescans,
            "parser_rejections": parser_rejections,
            "conclusion": (
                "The entire 43-bit one-orbit ansatz is exhausted: it contains no witness and has "
                "minimum burden 2. Its 86 optima are exactly the 43 rotations of a step-27 interval "
                "of 24 ones and the 43 rotations of an interval of 25 ones. The publisher seed is "
                "one length-24 optimum; its two radius-two minimizers merely translate the interval "
                "endpoints and are isomorphic copies."
            ),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "report": str(output),
            "report_sha256": digest(output),
            "minimum_burden": payload_a["minimum_burden"],
            "minimum_model_count": payload_a["minimum_model_count"],
            "classification": dict(sorted(classifications.items())),
            "normal_form": EXPECTED_NORMAL_FORM,
            "direct_full_k5_rescans": len(direct_rescans),
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
