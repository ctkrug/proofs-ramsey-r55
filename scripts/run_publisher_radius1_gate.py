#!/usr/bin/env python3
"""Fail-closed provenance and complete radius-1 gate for Springer Data 4."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


URL = "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt"
BODY_SHA256 = "c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990"
BODY_BYTES = 3812
EXPECTED_TITLE = "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"
EXPECTED_ZERO = [[6, 12, 17, 36, 42], [6, 12, 31, 36, 42]]
EXPECTED_ONE: list[list[int]] = []
EXPECTED_CANONICAL = {
    6: "ee2269437c3ba4cd8cde512768489089a5865ab701b38e8716acaddcdd07c3a7",
    12: "3f16d9a422f89c250bebd7d50fa6cb4006de0655513bac24f34232d2620c623f",
    36: "3f16d9a422f89c250bebd7d50fa6cb4006de0655513bac24f34232d2620c623f",
    42: "ee2269437c3ba4cd8cde512768489089a5865ab701b38e8716acaddcdd07c3a7",
}
RETRIEVALS = [
    {
        "body": "sources/retrievals/springer_supplementary_data4_audit1.txt",
        "headers": "sources/retrievals/springer_supplementary_data4_audit1.headers",
        "headers_sha256": "812897cabc7983657512723c9063a05844bc3001a003dcdb2fcf45a4b8534b1b",
        "transfer": ".proof-experiments/20260720-235158-0cfef1/stdout.txt",
        "transfer_sha256": "5d885accd3f22be27f69ea87d8c4d48df48d5c68094120aa3894fb8fc04eb1ca",
        "experiment": ".proof-experiments/20260720-235158-0cfef1/experiment.json",
        "experiment_sha256": "ed93b112680e9bbb970464d1888ed217f9b75131083f2ff2a244ca99b2a6a9f7",
    },
    {
        "body": "sources/retrievals/springer_supplementary_data4_audit2.txt",
        "headers": "sources/retrievals/springer_supplementary_data4_audit2.headers",
        "headers_sha256": "e918b8b4cf10807af426a63c775f47bf2ecaaae0acea1d4e52fda6c62536f7f6",
        "transfer": ".proof-experiments/20260720-235208-a7e84e/stdout.txt",
        "transfer_sha256": "d874ded0b3d4109577717cf06dcaf8d4f59fe44a72ddb98ab4795b362831fb23",
        "experiment": ".proof-experiments/20260720-235208-a7e84e/experiment.json",
        "experiment_sha256": "a73b7886b1512efe823143de17bc45327b1588ae016242849e6d7bdf121bf052",
    },
]


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def require_file(root: Path, relative: str, expected_sha256: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"missing or escaping linked artifact: {relative}")
    if digest(path) != expected_sha256:
        raise ValueError(f"linked artifact hash mismatch: {relative}")
    return path


def parse_headers(raw: bytes) -> tuple[int, dict[str, list[str]]]:
    blocks = [block for block in raw.decode("iso-8859-1").replace("\r\n", "\n").split("\n\n") if block.strip()]
    if not blocks:
        raise ValueError("empty HTTP header capture")
    lines = blocks[-1].splitlines()
    status_fields = lines[0].split()
    if len(status_fields) < 2 or not status_fields[0].startswith("HTTP/"):
        raise ValueError("malformed HTTP status line")
    headers: dict[str, list[str]] = {}
    for line in lines[1:]:
        if ":" not in line:
            raise ValueError("malformed HTTP header field")
        name, value = line.split(":", 1)
        headers.setdefault(name.strip().lower(), []).append(value.strip())
    return int(status_fields[1]), headers


def parse_transfer(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if text.endswith("\\n"):
        text = text[:-2]
    return json.loads(text)


def validate_admitted_body(raw: bytes) -> None:
    if len(raw) != BODY_BYTES or digest_bytes(raw) != BODY_SHA256:
        raise ValueError("body does not match the frozen publisher object")
    if raw.splitlines()[0].decode("ascii") != EXPECTED_TITLE:
        raise ValueError("body title does not match the frozen publisher object")


def validate_retrieval(root: Path, descriptor: dict[str, str]) -> dict[str, object]:
    body = require_file(root, descriptor["body"], BODY_SHA256)
    validate_admitted_body(body.read_bytes())
    headers_path = require_file(root, descriptor["headers"], descriptor["headers_sha256"])
    transfer_path = require_file(root, descriptor["transfer"], descriptor["transfer_sha256"])
    experiment_path = require_file(root, descriptor["experiment"], descriptor["experiment_sha256"])
    status, headers = parse_headers(headers_path.read_bytes())
    transfer = parse_transfer(transfer_path)
    experiment = json.loads(experiment_path.read_text(encoding="utf-8"))
    required_transfer = {
        "http_code": 200,
        "response_code": 200,
        "url_effective": URL,
        "size_download": BODY_BYTES,
        "ssl_verify_result": 0,
        "proxy_ssl_verify_result": 0,
        "content_type": "application/octet-stream",
        "num_redirects": 0,
        "scheme": "HTTPS",
    }
    for field, expected in required_transfer.items():
        if transfer.get(field) != expected:
            raise ValueError(f"transfer field {field} mismatch in {descriptor['transfer']}")
    if status != 200 or headers.get("content-type") != ["application/octet-stream"]:
        raise ValueError("header status or content type mismatch")
    if headers.get("content-length") != [str(BODY_BYTES)]:
        raise ValueError("header content length mismatch")
    if experiment.get("returncode") != 0 or experiment.get("timed_out") is not False:
        raise ValueError("retrieval experiment did not complete successfully")
    if experiment.get("source_urls") != [URL] or URL not in experiment.get("command", []):
        raise ValueError("retrieval experiment source/command mismatch")
    if experiment.get("artifacts", {}).get("stdout.txt") != descriptor["transfer_sha256"]:
        raise ValueError("retrieval experiment does not link its transfer stdout")
    if experiment.get("artifacts", {}).get("stderr.txt") != hashlib.sha256(b"").hexdigest():
        raise ValueError("retrieval stderr was not empty")
    return {
        "body": {"path": descriptor["body"], "bytes": body.stat().st_size, "sha256": digest(body)},
        "headers": {"path": descriptor["headers"], "bytes": headers_path.stat().st_size, "sha256": digest(headers_path)},
        "transfer": {"path": descriptor["transfer"], "sha256": digest(transfer_path), "selected_fields": required_transfer},
        "experiment": {"path": descriptor["experiment"], "sha256": digest(experiment_path), "id": experiment["id"]},
    }


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    if result.stderr:
        raise RuntimeError(f"unexpected checker stderr: {result.stderr}")
    return json.loads(result.stdout)


def expect_rejection(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode == 0:
        raise AssertionError(f"malformed input was accepted: {command}")
    return result.stderr.strip().splitlines()[-1]


def raw_matrix_bytes(matrix: list[list[int]]) -> bytes:
    return (EXPECTED_TITLE + "\n" + "\n".join(" ".join(map(str, row)) for row in matrix) + "\n").encode("ascii")


def matrix_from_raw(raw: bytes) -> list[list[int]]:
    lines = raw.decode("ascii").splitlines()
    return [[int(value) for value in line.split(" ")] for line in lines[1:]]


def graph6(matrix: list[list[int]]) -> bytes:
    n = len(matrix)
    if n > 62:
        raise ValueError("only short graph6 is supported")
    bits = [matrix[low][high] for high in range(1, n) for low in range(high)]
    bits.extend([0] * ((-len(bits)) % 6))
    encoded = [n + 63]
    for offset in range(0, len(bits), 6):
        value = 0
        for bit in bits[offset : offset + 6]:
            value = 2 * value + bit
        encoded.append(value + 63)
    return bytes(encoded)


def normalized(payload: dict[str, object]) -> dict[str, object]:
    source = dict(payload["source"])
    source.pop("upper_triangle_sha256", None)
    return {"source": source, "seed": payload["seed"], "radius1": payload.get("radius1")}


def score(item: dict[str, object]) -> int:
    return len(item["zero_k5"]) + len(item["one_k5"])


def family_summary(ledger: list[dict[str, object]], predicate, predicate_text: str) -> dict[str, object]:
    selected = [item for item in ledger if predicate(item["edge"])]
    minimum = min(score(item) for item in selected)
    return {
        "predicate": predicate_text,
        "flips": len(selected),
        "minimum_total_burden": minimum,
        "score_histogram": {str(key): value for key, value in sorted(Counter(score(item) for item in selected).items())},
        "minimizers": [item for item in selected if score(item) == minimum],
    }


def main() -> int:
    if len(sys.argv) != 7:
        raise SystemExit("usage: run_publisher_radius1_gate.py CHECKER_A CHECKER_B_C BODY1 BODY2 CORPUS_REPORT OUTPUT")
    checker_a = Path(sys.argv[1]).resolve()
    checker_b_source = Path(sys.argv[2]).resolve()
    body1 = Path(sys.argv[3]).resolve()
    body2 = Path(sys.argv[4]).resolve()
    corpus_report_path = Path(sys.argv[5]).resolve()
    output = Path(sys.argv[6]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    root = Path.cwd().resolve()
    if body1 != (root / RETRIEVALS[0]["body"]).resolve() or body2 != (root / RETRIEVALS[1]["body"]).resolve():
        raise ValueError("body arguments are not the two frozen retrieval paths")

    retrievals = [validate_retrieval(root, descriptor) for descriptor in RETRIEVALS]
    if body1.read_bytes() != body2.read_bytes():
        raise AssertionError("the two publisher retrieval bodies differ")
    corpus_report = json.loads(corpus_report_path.read_text(encoding="utf-8"))
    if corpus_report.get("status") != "corpus_control_pass" or corpus_report.get("canonical_distinct_classes") != 656:
        raise ValueError("authenticated supplied-656 report is not admitted")
    corpus_labels: dict[str, dict[str, object]] = {}
    for entry in corpus_report["per_record_manifest"]:
        for kind in ("source", "complement"):
            corpus_labels[entry[f"{kind}_canonical_sha256"]] = {"record": entry["record"], "kind": kind}

    compiler = shutil.which("gcc")
    labelg = shutil.which("nauty-labelg")
    if compiler is None or labelg is None:
        raise RuntimeError("gcc and nauty-labelg are required")
    with tempfile.TemporaryDirectory(prefix="r55-publisher-radius1-") as temporary:
        temp = Path(temporary)
        checker_b = temp / "publisher_radius1_b"
        compile_command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(checker_b_source), "-o", str(checker_b)]
        subprocess.run(compile_command, check=True)
        base_a = [sys.executable, str(checker_a), "--input", str(body1)]
        base_b = [str(checker_b), "--input", str(body1)]
        payload_a = run_json(base_a)
        payload_b = run_json(base_b)
        if normalized(payload_a) != normalized(payload_b):
            raise AssertionError("independent publisher checkers disagree on the complete radius-1 ledger")
        if payload_a["seed"] != {"zero_k5": EXPECTED_ZERO, "one_k5": EXPECTED_ONE}:
            raise AssertionError("publisher seed conflict identity mismatch")
        if payload_a["source"]["n"] != 43 or payload_a["source"]["edges"] != 454:
            raise AssertionError("publisher seed order or edge count mismatch")
        ledger = payload_a["radius1"]
        if len(ledger) != 903 or [item["edge"] for item in ledger] != [[u, v] for u in range(43) for v in range(u + 1, 43)]:
            raise AssertionError("radius-1 ledger does not enumerate all 903 edges in the frozen order")

        intersection = sorted(set(EXPECTED_ZERO[0]).intersection(EXPECTED_ZERO[1]))
        families = {
            "all_edges": family_summary(ledger, lambda edge: True, "0 <= u < v < 43"),
            "nonstar_relative_to_deletion_6": family_summary(ledger, lambda edge: 6 not in edge, "u != 6 and v != 6"),
            "avoid_all_shared_conflict_vertices": family_summary(
                ledger,
                lambda edge: not set(edge).intersection(intersection),
                "{u,v} intersection {6,12,36,42} is empty",
            ),
        }
        expected_families = {
            "all_edges": (903, 2, [[6, 12], [36, 42]]),
            "nonstar_relative_to_deletion_6": (861, 2, [[36, 42]]),
            "avoid_all_shared_conflict_vertices": (741, 3, [[0, 37], [5, 11], [10, 16], [16, 22], [21, 27], [26, 32], [32, 38]]),
        }
        for name, (count, minimum, minimizers) in expected_families.items():
            observed = families[name]
            if (observed["flips"], observed["minimum_total_burden"], [item["edge"] for item in observed["minimizers"]]) != (count, minimum, minimizers):
                raise AssertionError(f"family acceptance target mismatch: {name}")

        original_matrix = matrix_from_raw(body1.read_bytes())
        semantic_mutations: dict[str, object] = {}
        for name, value, field in (("forced_one_k5", 1, "one_k5"), ("forced_zero_k5", 0, "zero_k5")):
            matrix = [row[:] for row in original_matrix]
            for u in range(5):
                for v in range(u + 1, 5):
                    matrix[u][v] = matrix[v][u] = value
            path = temp / f"{name}.txt"
            path.write_bytes(raw_matrix_bytes(matrix))
            result_a = run_json([sys.executable, str(checker_a), "--input", str(path), "--seed-only"])
            result_b = run_json([str(checker_b), "--input", str(path), "--seed-only"])
            if normalized(result_a) != normalized(result_b) or [0, 1, 2, 3, 4] not in result_a["seed"][field]:
                raise AssertionError(f"semantic mutation failed: {name}")
            semantic_mutations[name] = {
                "target": [0, 1, 2, 3, 4],
                "zero_count": len(result_a["seed"]["zero_k5"]),
                "one_count": len(result_a["seed"]["one_k5"]),
                "independent_agreement": True,
            }

        malformed: dict[str, object] = {}
        malformed_bytes: dict[str, bytes] = {}
        lines = body1.read_bytes().splitlines(keepends=True)
        changed = bytearray(body1.read_bytes())
        first_zero = changed.find(b"0", changed.find(b"\n") + 1)
        changed[first_zero] = ord("x")
        malformed_bytes["nonbinary"] = bytes(changed)
        malformed_bytes["short_row"] = b"".join([lines[0], lines[1].rsplit(b" ", 1)[0] + b"\n", *lines[2:]])
        matrix = [row[:] for row in original_matrix]
        matrix[0][0] = 1
        malformed_bytes["nonzero_diagonal"] = raw_matrix_bytes(matrix)
        matrix = [row[:] for row in original_matrix]
        matrix[0][1] ^= 1
        malformed_bytes["asymmetric"] = raw_matrix_bytes(matrix)
        malformed_bytes["substituted_gist"] = (root / "inputs/k43_two_conflict_gist.txt").read_bytes()
        for name, raw in malformed_bytes.items():
            path = temp / f"malformed-{name}.txt"
            path.write_bytes(raw)
            malformed[name] = {
                "checker_a": expect_rejection([sys.executable, str(checker_a), "--input", str(path), "--seed-only"]),
                "checker_b": expect_rejection([str(checker_b), "--input", str(path), "--seed-only"]),
            }
        matrix = [row[:] for row in original_matrix]
        matrix[0][1] ^= 1
        matrix[1][0] ^= 1
        try:
            validate_admitted_body(raw_matrix_bytes(matrix))
        except ValueError as error:
            malformed["valid_matrix_but_altered_body_rejected_by_source_gate"] = str(error)
        else:
            raise AssertionError("source gate accepted an altered but structurally valid matrix")

        score_representatives: dict[int, dict[str, object]] = {}
        for item in ledger:
            score_representatives.setdefault(score(item), item)
        selected_edges = {tuple(item["edge"]) for item in score_representatives.values()}
        for family in families.values():
            selected_edges.update(tuple(item["edge"]) for item in family["minimizers"])
        direct_rescans = []
        ledger_by_edge = {tuple(item["edge"]): item for item in ledger}
        for u, v in sorted(selected_edges):
            matrix = [row[:] for row in original_matrix]
            matrix[u][v] ^= 1
            matrix[v][u] ^= 1
            path = temp / f"rescan-{u}-{v}.txt"
            path.write_bytes(raw_matrix_bytes(matrix))
            result_a = run_json([sys.executable, str(checker_a), "--input", str(path), "--seed-only"])
            result_b = run_json([str(checker_b), "--input", str(path), "--seed-only"])
            expected_seed = {key: ledger_by_edge[(u, v)][key] for key in ("zero_k5", "one_k5")}
            if result_a["seed"] != expected_seed or result_b["seed"] != expected_seed:
                raise AssertionError(f"direct rescan mismatch at edge {(u, v)}")
            direct_rescans.append({"edge": [u, v], "burden": score(ledger_by_edge[(u, v)]), "identity_agreement": True})

        deletion_lines = []
        for vertex in intersection:
            keep = [u for u in range(43) if u != vertex]
            deleted = [[original_matrix[u][v] for v in keep] for u in keep]
            deletion_lines.append(graph6(deleted))
        deletion_input = temp / "deletions.g6"
        deletion_output = temp / "deletions-canonical.g6"
        deletion_input.write_bytes(b"\n".join(deletion_lines) + b"\n")
        subprocess.run([labelg, "-q", str(deletion_input), str(deletion_output)], check=True)
        canonical_lines = deletion_output.read_bytes().splitlines()
        if len(canonical_lines) != 4:
            raise AssertionError("nauty did not emit four deletion labels")
        deletions = []
        for vertex, line in zip(intersection, canonical_lines, strict=True):
            canonical_sha256 = digest_bytes(line + b"\n")
            if canonical_sha256 != EXPECTED_CANONICAL[vertex] or canonical_sha256 not in corpus_labels:
                raise AssertionError(f"deletion {vertex} canonical membership mismatch")
            deletions.append({
                "vertex": vertex,
                "valid_from_complete_seed_violation_projection": True,
                "canonical_sha256": canonical_sha256,
                "supplied_656_membership": corpus_labels[canonical_sha256],
            })

        report = {
            "schema_version": 1,
            "status": "publisher_seed_radius1_pass",
            "claim_scope": "the frozen Springer Supplementary Data 4 K43 seed and exactly its 903 one-edge flips; not a larger Hamming ball, global optimum, Ramsey witness, bound, or complete order-42 census",
            "source": {
                "authority": "Springer publisher-controlled static-content URL",
                "url": URL,
                "body_sha256": BODY_SHA256,
                "body_bytes": BODY_BYTES,
                "dual_retrieval_byte_identity": True,
                "retrievals": retrievals,
            },
            "checker_a": {"path": str(checker_a), "sha256": digest(checker_a), "method": payload_a["checker"]},
            "checker_b": {
                "path": str(checker_b_source),
                "source_sha256": digest(checker_b_source),
                "compiled_binary_sha256": digest(checker_b),
                "compile_command": compile_command[:-1] + ["<temporary>/publisher_radius1_b"],
                "compiler_version": subprocess.run([compiler, "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0],
                "method": payload_b["checker"],
            },
            "independence": "Checker A parses raw publisher whitespace in Python and scans C(43,5) subsets once with exact one-edge deltas; Checker B separately parses fixed raw byte positions in C and recursively enumerates graph/complement K5s afresh for each flip.",
            "seed": {
                **payload_a["source"],
                **payload_a["seed"],
                "conflict_intersection": intersection,
                "conflict_union": sorted(set(EXPECTED_ZERO[0]).union(EXPECTED_ZERO[1])),
            },
            "valid_deletions": deletions,
            "authenticated_supplied_corpus": {
                "path": str(corpus_report_path),
                "sha256": digest(corpus_report_path),
                "scope": corpus_report["claim_scope"],
            },
            "semantic_mutations": semantic_mutations,
            "source_and_parser_rejections": malformed,
            "families": families,
            "complete_flip_ledger": [dict(item, total_burden=score(item)) for item in ledger],
            "complete_ledger_independent_identity_agreement": True,
            "direct_rescan_controls": {
                "selection": "every distinct global burden class representative plus every minimizer from all three recorded families",
                "count": len(direct_rescans),
                "results": direct_rescans,
            },
            "canonicalizer": {
                "path": labelg,
                "version_probe": subprocess.run([labelg], text=True, capture_output=True).stderr.splitlines()[1].strip(),
            },
        }
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "report": str(output),
            "report_sha256": digest(output),
            "seed_conflicts": report["seed"]["zero_k5"],
            "family_minima": {name: {"flips": item["flips"], "minimum": item["minimum_total_burden"], "edges": [entry["edge"] for entry in item["minimizers"]]} for name, item in families.items()},
            "direct_rescans": len(direct_rescans),
            "valid_deletions": deletions,
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
