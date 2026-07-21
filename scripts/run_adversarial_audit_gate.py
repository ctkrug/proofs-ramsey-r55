#!/usr/bin/env python3
"""Independent, fail-closed audit of the retained R(5,5) radius-two claims.

This file deliberately does not import any retained R55 parser, checker,
constraint generator, pair-index function, or delta recurrence.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import itertools
import json
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time


N = 43
EXPECTED_BYTES = 3812
EXPECTED_SHA256 = "c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990"
TITLE = "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"
RANDOM_SEED = 0x55_43_2026


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def parse_matrix_bytes(raw: bytes) -> list[list[int]]:
    if not raw.endswith(b"\n"):
        raise ValueError("matrix lacks final LF")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("matrix is not ASCII") from error
    if len(lines) != N + 1 or lines[0] != TITLE:
        raise ValueError("title or row count mismatch")
    matrix: list[list[int]] = []
    for row_index, line in enumerate(lines[1:]):
        fields = line.split()
        if len(fields) != N or any(field not in {"0", "1"} for field in fields):
            raise ValueError(f"invalid row {row_index}")
        matrix.append([int(field) for field in fields])
    for u in range(N):
        if matrix[u][u] != 0:
            raise ValueError("nonzero diagonal")
        for v in range(u + 1, N):
            if matrix[u][v] != matrix[v][u]:
                raise ValueError("asymmetric matrix")
    return matrix


def matrix_bytes(matrix: list[list[int]]) -> bytes:
    return (TITLE + "\n" + "\n".join(" ".join(map(str, row)) for row in matrix) + "\n").encode("ascii")


def rows_from_matrix(matrix: list[list[int]]) -> list[int]:
    rows = [0] * N
    for u in range(N):
        for v in range(N):
            if matrix[u][v]:
                rows[u] |= 1 << v
    return rows


def violation_identities(matrix: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    rows = rows_from_matrix(matrix)
    zero: list[list[int]] = []
    one: list[list[int]] = []
    for vertices in itertools.combinations(range(N), 5):
        mask = sum(1 << vertex for vertex in vertices)
        twice_edges = sum((rows[vertex] & mask).bit_count() for vertex in vertices)
        if twice_edges == 0:
            zero.append(list(vertices))
        elif twice_edges == 20:
            one.append(list(vertices))
    return zero, one


def edges_lexicographic() -> list[tuple[int, int]]:
    return [(u, v) for u in range(N) for v in range(u + 1, N)]


def pair_index(first: int, second: int, edge_count: int) -> int:
    if not 0 <= first < second < edge_count:
        raise ValueError("invalid edge-index pair")
    return first * (2 * edge_count - first - 1) // 2 + second - first - 1


def pair_at(index: int, edge_count: int) -> tuple[int, int]:
    if not 0 <= index < edge_count * (edge_count - 1) // 2:
        raise ValueError("invalid pair index")
    cursor = 0
    for first in range(edge_count - 1):
        width = edge_count - first - 1
        if index < cursor + width:
            return first, first + 1 + index - cursor
        cursor += width
    raise AssertionError("pair inverse fell through")


def edited(matrix: list[list[int]], changed_edges: list[tuple[int, int]]) -> list[list[int]]:
    result = [row[:] for row in matrix]
    for u, v in changed_edges:
        result[u][v] ^= 1
        result[v][u] ^= 1
    return result


def rotated(matrix: list[list[int]], shift: int) -> list[list[int]]:
    result = [[0] * N for _ in range(N)]
    for u in range(N):
        for v in range(N):
            result[(u + shift) % N][(v + shift) % N] = matrix[u][v]
    return result


def variable_for_distance(u: int, v: int, distance: int) -> int | None:
    delta = (v - u) % N
    if delta == distance:
        return u
    if delta == N - distance:
        return v
    return None


def derive_one_orbit_constraints(matrix: list[list[int]]) -> tuple[list[dict[str, object]], Counter[tuple[int, tuple[int, ...]]], dict[str, int]]:
    active: list[dict[str, object]] = []
    multiplicities: Counter[tuple[int, tuple[int, ...]]] = Counter()
    accounting = Counter()
    for vertices in itertools.combinations(range(N), 5):
        accounting["five_sets_examined"] += 1
        variables: list[int] = []
        fixed: list[int] = []
        for u, v in itertools.combinations(vertices, 2):
            variable = variable_for_distance(u, v, 6)
            if variable is None:
                fixed.append(matrix[u][v])
            else:
                variables.append(variable)
        variables_tuple = tuple(sorted(variables))
        zero_possible = 1 not in fixed
        one_possible = 0 not in fixed
        if zero_possible:
            if not variables_tuple:
                raise AssertionError(f"unavoidable all-zero K5 at {vertices}")
            item = (1, variables_tuple)
            multiplicities[item] += 1
            active.append({"vertices": list(vertices), "color": 0, "variables": list(variables_tuple)})
            accounting["zero_active"] += 1
        if one_possible:
            if not variables_tuple:
                raise AssertionError(f"unavoidable all-one K5 at {vertices}")
            item = (0, variables_tuple)
            multiplicities[item] += 1
            active.append({"vertices": list(vertices), "color": 1, "variables": list(variables_tuple)})
            accounting["one_active"] += 1
        if not zero_possible and not one_possible:
            accounting["fixed_both_colors_inactive"] += 1
        elif zero_possible and one_possible:
            accounting["no_fixed_edges_double_active"] += 1
        else:
            accounting["single_color_active_five_sets"] += 1
    if accounting["five_sets_examined"] != 962_598:
        raise AssertionError("C(43,5) accounting mismatch")
    if sum((accounting["fixed_both_colors_inactive"], accounting["single_color_active_five_sets"], accounting["no_fixed_edges_double_active"])) != 962_598:
        raise AssertionError("five-set disposition accounting mismatch")
    return active, multiplicities, dict(accounting)


def normalized_shape(indices: tuple[int, ...]) -> tuple[int, ...]:
    # 8 is 27^{-1} mod 43, so u=27t.
    transformed = tuple((8 * value) % N for value in indices)
    return min(tuple(sorted((value - anchor) % N for value in transformed)) for anchor in transformed)


def reduced_burden(word: str, raw_constraints: list[dict[str, object]]) -> int:
    bits = [bit == "1" for bit in word]
    total = 0
    for item in raw_constraints:
        values = [bits[int(index)] for index in item["variables"]]
        if item["color"] == 0:
            total += not any(values)
        else:
            total += all(values)
    return int(total)


def interval_class(word: str) -> str | None:
    transformed = [word[(27 * t) % N] for t in range(N)]
    transitions = sum(transformed[index] != transformed[(index + 1) % N] for index in range(N))
    ones = transformed.count("1")
    if transitions == 2 and ones in {24, 25}:
        return f"step27_cyclic_interval_length_{ones}"
    return None


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    if result.stderr:
        raise RuntimeError(f"unexpected stderr from {' '.join(command)}: {result.stderr}")
    return json.loads(result.stdout)


def rejected_by_cpp(executable: Path, path: Path) -> bool:
    return subprocess.run([str(executable), str(path)], capture_output=True).returncode != 0


def main() -> int:
    if len(sys.argv) != 9:
        raise SystemExit(
            "usage: run_adversarial_audit_gate.py BITSET_CPP BODY1 BODY2 "
            "RADIUS1_REPORT RADIUS2_REPORT RADIUS2_LEDGER DISTANCE6_REPORT OUTPUT"
        )
    cpp_source, body1, body2, radius1_path, radius2_path, ledger_path, distance6_path, output = map(Path, sys.argv[1:])
    body1_raw = body1.read_bytes()
    body2_raw = body2.read_bytes()
    if len(body1_raw) != EXPECTED_BYTES or sha256(body1_raw).hexdigest() != EXPECTED_SHA256:
        raise AssertionError("first frozen publisher body identity mismatch")
    if body1_raw != body2_raw:
        raise AssertionError("dual publisher retrieval bodies differ")

    matrix = parse_matrix_bytes(body1_raw)
    edge_count = sum(matrix[u][v] for u in range(N) for v in range(u + 1, N))
    zero_k5, one_k5 = violation_identities(matrix)
    expected_zero = [[6, 12, 17, 36, 42], [6, 12, 31, 36, 42]]
    if edge_count != 454 or zero_k5 != expected_zero or one_k5:
        raise AssertionError("seed structure or exact conflicts mismatch")

    compiler = shutil.which("clang++") or shutil.which("g++")
    if compiler is None:
        raise RuntimeError("a C++20 compiler is required")
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="r55-adversarial-audit-") as temporary_name:
        temporary = Path(temporary_name)
        executable = temporary / "adversarial_radius2_bitset"
        recomputed_ledger = temporary / "radius2.u16le"
        subprocess.run(
            [compiler, "-std=c++20", "-O3", "-Wall", "-Wextra", "-Werror", str(cpp_source), "-o", str(executable)],
            check=True,
        )
        bitset_summary = run_json([str(executable), str(body1), str(recomputed_ledger)])
        if recomputed_ledger.read_bytes() != ledger_path.read_bytes():
            raise AssertionError("independent radius-two ledger differs byte-for-byte")
        recomputed_ledger_sha256 = digest(recomputed_ledger)

        radius1 = json.loads(radius1_path.read_text(encoding="utf-8"))
        provenance_records: list[dict[str, object]] = []
        admitted_bodies = {body1.resolve(), body2.resolve()}
        for retrieval in radius1["source"]["retrievals"]:
            body_record = retrieval["body"]
            header_record = retrieval["headers"]
            experiment_record = retrieval["experiment"]
            transfer_record = retrieval["transfer"]
            recorded_body = Path(body_record["path"]).resolve()
            recorded_headers = Path(header_record["path"]).resolve()
            recorded_experiment = Path(experiment_record["path"]).resolve()
            recorded_transfer = Path(transfer_record["path"]).resolve()
            if recorded_body not in admitted_bodies:
                raise AssertionError("provenance record points at an unadmitted body")
            for record, path in (
                (body_record, recorded_body),
                (header_record, recorded_headers),
                (experiment_record, recorded_experiment),
                (transfer_record, recorded_transfer),
            ):
                if digest(path) != record["sha256"]:
                    raise AssertionError(f"provenance artifact hash mismatch: {path}")
            headers_text = recorded_headers.read_text(encoding="ascii").lower()
            if not headers_text.startswith("http/2 200"):
                raise AssertionError("retrieval header lacks HTTP/2 200")
            if "content-type: application/octet-stream" not in headers_text:
                raise AssertionError("retrieval content type mismatch")
            if f"content-length: {EXPECTED_BYTES}" not in headers_text:
                raise AssertionError("retrieval content length mismatch")
            experiment = json.loads(recorded_experiment.read_text(encoding="utf-8"))
            transfer = json.loads(recorded_transfer.read_text(encoding="utf-8"))
            if experiment["returncode"] != 0 or experiment["command"][0] != "curl":
                raise AssertionError("retrieval experiment was not a successful curl run")
            if experiment["source_urls"] != [radius1["source"]["url"]]:
                raise AssertionError("retrieval experiment source URL mismatch")
            expected_transfer = {
                "http_code": 200,
                "response_code": 200,
                "num_redirects": 0,
                "scheme": "HTTPS",
                "size_download": EXPECTED_BYTES,
                "ssl_verify_result": 0,
                "proxy_ssl_verify_result": 0,
                "content_type": "application/octet-stream",
                "url_effective": radius1["source"]["url"],
            }
            for field, expected in expected_transfer.items():
                if transfer[field] != expected:
                    raise AssertionError(f"retrieval transfer field mismatch: {field}")
            provenance_records.append({
                "body": {"path": str(recorded_body), "bytes": recorded_body.stat().st_size, "sha256": digest(recorded_body)},
                "headers": {"path": str(recorded_headers), "sha256": digest(recorded_headers), "http_status": 200},
                "experiment": {"path": str(recorded_experiment), "sha256": digest(recorded_experiment), "returncode": 0},
                "transfer": expected_transfer,
            })
        if len(provenance_records) != 2:
            raise AssertionError("expected exactly two provenance records")
        retained_radius_one = radius1["families"]["all_edges"]
        expected_radius_one_minimizers = [
            {"edge_index": edges_lexicographic().index(tuple(item["edge"])), "edge": item["edge"]}
            for item in retained_radius_one["minimizers"]
        ]
        if bitset_summary["edge_count"] != retained_radius_one["flips"]:
            raise AssertionError("radius-one cardinality mismatch")
        if bitset_summary["radius_one_minimum"] != retained_radius_one["minimum_total_burden"]:
            raise AssertionError("radius-one minimum mismatch")
        if bitset_summary["radius_one_minimizers"] != expected_radius_one_minimizers:
            raise AssertionError("radius-one minimizer mismatch")
        if bitset_summary["radius_one_histogram"] != retained_radius_one["score_histogram"]:
            raise AssertionError("radius-one histogram mismatch")

        radius2 = json.loads(radius2_path.read_text(encoding="utf-8"))
        retained_family = radius2["families"]["all_two_edge_flips"]
        retained_strict = radius2["families"]["deletion_remainder_change_for_every_valid_deletion"]
        scalar_expectations = {
            "pair_count": retained_family["pairs"],
            "minimum": retained_family["minimum_total_burden"],
            "strict_pair_count": retained_strict["pairs"],
            "strict_minimum": retained_strict["minimum_total_burden"],
        }
        for field, expected in scalar_expectations.items():
            if bitset_summary[field] != expected:
                raise AssertionError(f"radius-two scalar mismatch at {field}")
        if bitset_summary["histogram"] != retained_family["score_histogram"]:
            raise AssertionError("global radius-two histogram mismatch")
        if bitset_summary["strict_histogram"] != retained_strict["score_histogram"]:
            raise AssertionError("strict-family radius-two histogram mismatch")
        if bitset_summary["minimizers"] != [
            {"edge_indices": item["edge_indices"], "edges": item["edges"]}
            for item in retained_family["minimizers"]
        ]:
            raise AssertionError("radius-two minimizer mismatch")

        malformed: dict[str, bytes] = {}
        changed = bytearray(body1_raw)
        first_data = changed.index(b"\n") + 1
        changed[first_data] = ord("x")
        malformed["nonbinary"] = bytes(changed)
        malformed["shortened"] = body1_raw[:-2]
        diagonal = [row[:] for row in matrix]
        diagonal[0][0] = 1
        malformed["nonzero_diagonal"] = matrix_bytes(diagonal)
        asymmetric = [row[:] for row in matrix]
        asymmetric[0][1] ^= 1
        malformed["asymmetric"] = matrix_bytes(asymmetric)
        malformed["extra_line"] = body1_raw + b"0\n"
        parser_controls: dict[str, object] = {}
        for name, raw in malformed.items():
            path = temporary / f"malformed-{name}.txt"
            path.write_bytes(raw)
            python_rejected = False
            try:
                parse_matrix_bytes(raw)
            except ValueError:
                python_rejected = True
            cpp_rejected = rejected_by_cpp(executable, path)
            if not python_rejected or not cpp_rejected:
                raise AssertionError(f"malformed control accepted: {name}")
            parser_controls[name] = {"python_rejected": True, "cpp_rejected": True}

        semantic_controls: dict[str, object] = {}
        for name, vertices, color in (
            ("forced_clique", [0, 1, 2, 3, 4], 1),
            ("forced_coclique", [5, 6, 7, 8, 9], 0),
        ):
            mutation = [row[:] for row in matrix]
            for u, v in itertools.combinations(vertices, 2):
                mutation[u][v] = mutation[v][u] = color
            path = temporary / f"{name}.txt"
            path.write_bytes(matrix_bytes(mutation))
            zero, one = violation_identities(mutation)
            cpp = run_json([str(executable), str(path)])
            if name == "forced_clique" and vertices not in one:
                raise AssertionError("forced clique was not detected")
            if name == "forced_coclique" and vertices not in zero:
                raise AssertionError("forced coclique was not detected")
            if cpp["zero_k5"] != len(zero) or cpp["one_k5"] != len(one):
                raise AssertionError(f"semantic control disagreement: {name}")
            semantic_controls[name] = {
                "forced_vertices": vertices,
                "zero_k5_count": len(zero),
                "one_k5_count": len(one),
                "independent_count_agreement": True,
            }

        scores = [item[0] for item in struct.iter_unpack("<H", ledger_path.read_bytes())]
        edges = edges_lexicographic()
        if len(edges) != 903 or len(scores) != 407_253:
            raise AssertionError("edge or pair ledger cardinality mismatch")
        boundary_pairs = [(0, 1), (0, 902), (1, 2), (451, 452), (451, 902), (901, 902), (242, 347), (863, 887)]
        random_generator = random.Random(RANDOM_SEED)
        random_pairs = []
        while len(random_pairs) < 12:
            first, second = sorted(random_generator.sample(range(len(edges)), 2))
            if (first, second) not in boundary_pairs and (first, second) not in random_pairs:
                random_pairs.append((first, second))
        direct_rescans: list[dict[str, object]] = []
        for first, second in boundary_pairs + random_pairs:
            index = pair_index(first, second, len(edges))
            if pair_at(index, len(edges)) != (first, second):
                raise AssertionError("pair index inverse mismatch")
            zero, one = violation_identities(edited(matrix, [edges[first], edges[second]]))
            observed = len(zero) + len(one)
            if observed != scores[index]:
                raise AssertionError(f"direct rescan mismatch at pair {first},{second}")
            direct_rescans.append({
                "pair_index": index,
                "edge_indices": [first, second],
                "edges": [list(edges[first]), list(edges[second])],
                "burden": observed,
                "zero_k5": zero,
                "one_k5": one,
            })

    rotation_checks: list[dict[str, object]] = []
    for minimizer in bitset_summary["minimizers"]:
        changed_edges = [tuple(edge) for edge in minimizer["edges"]]
        candidate = edited(matrix, changed_edges)
        matching_shifts = [shift for shift in range(N) if candidate == rotated(matrix, shift)]
        if len(matching_shifts) != 1:
            raise AssertionError("edited minimizer is not a unique explicit rotation of the seed")
        claimed_representative = {16: -27, 27: 27}.get(matching_shifts[0], matching_shifts[0])
        rotation_checks.append({
            "edges": minimizer["edges"],
            "explicit_vertex_permutation": f"u -> u{claimed_representative:+d} mod 43",
            "shift_mod_43": matching_shifts[0],
            "all_1849_matrix_entries_equal": True,
        })
    if [item["shift_mod_43"] for item in rotation_checks] != [16, 27]:
        raise AssertionError("claimed -27/+27 rotations mismatch")

    orbit_profile = []
    for distance in range(1, 22):
        word = "".join(str(matrix[u][(u + distance) % N]) for u in range(N))
        orbit_profile.append({"distance": distance, "ones": word.count("1"), "word_u_order": word})
    exceptional = [item for item in orbit_profile if item["ones"] not in {0, N}]
    if len(exceptional) != 1 or exceptional[0]["distance"] != 6 or exceptional[0]["ones"] != 24:
        raise AssertionError("distance-orbit profile mismatch")

    active, multiplicities, five_set_accounting = derive_one_orbit_constraints(matrix)
    positive = sorted(indices for (polarity, indices), count in multiplicities.items() if polarity == 1)
    negative = sorted(indices for (polarity, indices), count in multiplicities.items() if polarity == 0)
    positive_counts = {multiplicities[(1, item)] for item in positive}
    negative_counts = {multiplicities[(0, item)] for item in negative}
    normal_form = {
        "positive_pair_shapes": [list(item) for item in sorted({normalized_shape(item) for item in positive})],
        "negative_triple_shapes": [list(item) for item in sorted({normalized_shape(item) for item in negative})],
    }
    if len(active) != 215 or len(multiplicities) != 129 or positive_counts != {2} or negative_counts != {1}:
        raise AssertionError("one-orbit clause cardinality or multiplicity mismatch")
    if normal_form != {"positive_pair_shapes": [[0, 18], [0, 20]], "negative_triple_shapes": [[0, 5, 24]]}:
        raise AssertionError("one-orbit normal form mismatch")

    distance6 = json.loads(distance6_path.read_text(encoding="utf-8"))
    retained_constraints = distance6["reduced_constraint_system"]
    if [list(item) for item in positive] != retained_constraints["positive_pairs"]:
        raise AssertionError("positive clause identity mismatch")
    if [list(item) for item in negative] != retained_constraints["negative_triples"]:
        raise AssertionError("negative clause identity mismatch")
    if normal_form != retained_constraints["normal_form"]:
        raise AssertionError("normal-form identity mismatch")

    retained_words = distance6["exact_result"]["minimum_words_u_order"]
    classification = Counter()
    for word in retained_words:
        if reduced_burden(word, active) != 2:
            raise AssertionError("retained optimum word does not have raw burden two")
        label = interval_class(word)
        if label is None:
            raise AssertionError("retained optimum word is not a claimed interval")
        classification[label] += 1
    if len(set(retained_words)) != 86 or classification != Counter({
        "step27_cyclic_interval_length_24": 43,
        "step27_cyclic_interval_length_25": 43,
    }):
        raise AssertionError("retained 86-word list or interval classification mismatch")

    report = {
        "schema_version": 1,
        "status": "adversarial_radius2_and_one_orbit_audit_pass",
        "claim_scope": "Independent audit of the frozen Springer seed, all 407253 radius-two pairs, and direct derivation of its 43-variable distance-six constraint system; completeness of the 86-word optimum set is certified separately.",
        "source": {
            "body_bytes": len(body1_raw),
            "body_sha256": sha256(body1_raw).hexdigest(),
            "dual_retrieval_byte_identity": True,
            "body_paths": [str(body1), str(body2)],
            "body2_sha256": digest(body2),
            "publisher_url": radius1["source"]["url"],
            "retrieval_provenance": provenance_records,
        },
        "matrix": {
            "order": N,
            "symmetric": True,
            "zero_diagonal": True,
            "edges": edge_count,
            "zero_k5": zero_k5,
            "one_k5": one_k5,
        },
        "radius_two": {
            "method": bitset_summary["checker"],
            "edge_order": "(u,v) lexicographic for 0 <= u < v < 43",
            "pair_order": "(first_edge_index,second_edge_index) lexicographic with first < second",
            "pair_index_formula": "i*(2E-i-1)/2 + j-i-1",
            "edge_count": len(edges_lexicographic()),
            "pair_count": bitset_summary["pair_count"],
            "minimum": bitset_summary["minimum"],
            "minimizers": bitset_summary["minimizers"],
            "histogram": bitset_summary["histogram"],
            "strict_predicate": "for every v in {6,12,36,42}, at least one edited edge is not incident to v",
            "strict_pair_count": bitset_summary["strict_pair_count"],
            "strict_minimum": bitset_summary["strict_minimum"],
            "strict_minimizers": bitset_summary["strict_minimizers"],
            "retained_ledger_sha256": digest(ledger_path),
            "recomputed_ledger_sha256": recomputed_ledger_sha256,
            "byte_for_byte_ledger_agreement": True,
            "direct_rescan_random_seed": RANDOM_SEED,
            "direct_rescans": direct_rescans,
        },
        "radius_one": {
            "method": bitset_summary["checker"],
            "flips": bitset_summary["edge_count"],
            "minimum": bitset_summary["radius_one_minimum"],
            "minimizers": bitset_summary["radius_one_minimizers"],
            "histogram": bitset_summary["radius_one_histogram"],
            "all_903_scores_match_retained_report": True,
        },
        "rotation_checks": rotation_checks,
        "distance_orbits": orbit_profile,
        "one_orbit_constraints": {
            "variables": "edge {u,u+6 mod 43} indexed by u",
            "five_set_accounting": five_set_accounting,
            "raw_active_five_sets": len(active),
            "unique_constraints": len(multiplicities),
            "positive_pair_count": len(positive),
            "positive_pair_multiplicity": sorted(positive_counts),
            "negative_triple_count": len(negative),
            "negative_triple_multiplicity": sorted(negative_counts),
            "normal_form": normal_form,
            "retained_86_words_each_directly_rechecked_at_burden_two": True,
            "retained_word_classification": dict(sorted(classification.items())),
            "completeness_dependency": "separate deterministic CNF plus checked proof log",
        },
        "controls": {
            "malformed_inputs": parser_controls,
            "semantic_mutations": semantic_controls,
            "ordering_boundaries_and_random_direct_rescans": len(direct_rescans),
        },
        "independence": {
            "parser": "line-oriented ASCII token parser written for this audit",
            "radius_two": "C++20 adjacency bitsets; each K5 is counted from its three smallest vertices and an edge in their common neighborhood",
            "direct_rescans": "Python exhaustive C(43,5) induced-edge counts",
            "constraints": "all C(43,5) five-sets rederived without retained fixed-edge tests",
            "imports_retained_checker_logic": False,
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "output": str(output),
        "output_sha256": digest(output),
        "elapsed_seconds": report["elapsed_seconds"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
