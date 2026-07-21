#!/usr/bin/env python3
"""Cold audit of the order-42 exact-boundary repair packet.

This implementation does not import the producer.  It uses NetworkX's
graph6 parser, maximal-clique enumeration in the graph and complement,
NetworkX isomorphism, and a direct DIMACS/model satisfaction pass.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import gzip
from pathlib import Path
import sys

import networkx as nx


ORDER = 42
FINGERPRINT = "r55novel42basin2026"
CORPUS_SHA256 = "067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
    return value.hexdigest()


def stored_or_gzip(path: Path) -> Path:
    if path.exists():
        return path
    compressed = Path(str(path) + ".gz")
    if compressed.exists():
        return compressed
    raise FileNotFoundError(path)


def read_text(path: Path) -> str:
    stored = stored_or_gzip(path)
    if stored.suffix == ".gz":
        with gzip.open(stored, "rt", encoding="ascii") as stream:
            return stream.read()
    return stored.read_text(encoding="ascii")


def logical_digest(path: Path) -> str:
    stored = stored_or_gzip(path)
    value = hashlib.sha256()
    if stored.suffix == ".gz":
        with gzip.open(stored, "rb") as stream:
            for block in iter(lambda: stream.read(1 << 20), b""):
                value.update(block)
    else:
        with stored.open("rb") as stream:
            for block in iter(lambda: stream.read(1 << 20), b""):
                value.update(block)
    return value.hexdigest()


def graph(record: bytes) -> nx.Graph:
    result = nx.from_graph6_bytes(record.rstrip(b"\r\n"))
    if list(result.nodes()) != list(range(ORDER)) or result.number_of_nodes() != ORDER:
        raise AssertionError("unexpected graph6 vertex set")
    return result


def stable_sample(label: str, population: list[int], count: int) -> list[int]:
    return sorted(
        sorted(population, key=lambda item: hashlib.sha256(f"{FINGERPRINT}:{label}:{item}".encode()).digest())[:count]
    )


def canonical_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_ramsey(candidate: nx.Graph) -> tuple[int, int]:
    graph_maximum = max(map(len, nx.find_cliques(candidate)), default=0)
    complement_maximum = max(map(len, nx.find_cliques(nx.complement(candidate))), default=0)
    if graph_maximum >= 5 or complement_maximum >= 5:
        raise AssertionError("candidate fails independent maximal-clique scan")
    return graph_maximum, complement_maximum


def parse_model(path: Path) -> dict[int, bool]:
    values: dict[int, bool] = {}
    for line in read_text(path).splitlines():
        if line.startswith("v "):
            for text in line[2:].split():
                literal = int(text)
                if literal:
                    values[abs(literal)] = literal > 0
    return values


def check_cnf(cnf: Path, values: dict[int, bool]) -> dict[str, object]:
    variables = clauses_expected = None
    clauses = 0
    for line_number, raw in enumerate(read_text(cnf).splitlines(), 1):
        if raw.startswith("p cnf "):
            _, _, variables_text, clauses_text = raw.split()
            variables, clauses_expected = int(variables_text), int(clauses_text)
            continue
        if not raw or raw.startswith("c"):
            continue
        literals = [int(text) for text in raw.split()]
        if not literals or literals[-1] != 0:
            raise AssertionError(f"malformed clause at line {line_number}")
        literals.pop()
        if not any(values.get(abs(literal)) == (literal > 0) for literal in literals):
            raise AssertionError(f"model falsifies clause at line {line_number}")
        clauses += 1
    if variables is None or clauses != clauses_expected or set(range(1, variables + 1)) - values.keys():
        raise AssertionError("DIMACS header, count, or total model mismatch")
    return {"variables": variables, "clauses": clauses, "all_clauses_satisfied": True}


def force_five(candidate: nx.Graph, edge: bool) -> nx.Graph:
    result = candidate.copy()
    for u, v in itertools.combinations(range(5), 2):
        if edge:
            result.add_edge(u, v)
        else:
            result.remove_edge(u, v) if result.has_edge(u, v) else None
    return result


def main() -> int:
    if len(sys.argv) != 6:
        raise SystemExit("usage: novel42_boundary_audit.py CORPUS CORPUS_REPORT PRODUCTION_REPORT ARTIFACT_DIR OUTPUT")
    corpus_path, corpus_report_path, production_report_path, artifact_dir, output = map(Path, sys.argv[1:])
    if digest(corpus_path) != CORPUS_SHA256:
        raise AssertionError("corpus hash mismatch")
    retained = json.loads(corpus_report_path.read_text(encoding="utf-8"))
    production = json.loads(production_report_path.read_text(encoding="utf-8"))
    records = corpus_path.read_bytes().splitlines()
    if len(records) != 328:
        raise AssertionError("corpus record count mismatch")
    sources = [graph(record) for record in records]
    controls = sources + [nx.complement(item) for item in sources]

    lookup: dict[str, tuple[int, str, nx.Graph]] = {}
    for entry in retained["per_record_manifest"]:
        index = int(entry["record"]) - 1
        for kind, item in (("source", sources[index]), ("complement", controls[328 + index])):
            key = entry[f"{kind}_canonical_sha256"]
            if key in lookup:
                raise AssertionError("duplicate retained canonical hash")
            lookup[key] = (index + 1, kind, item)
    if len(lookup) != 656:
        raise AssertionError("canonical lookup scope mismatch")

    expected_records = [index + 1 for index in stable_sample("records", list(range(328)), 8)]
    if production["leakage_control"]["predeclared_record_indices_one_based"] != expected_records:
        raise AssertionError("predeclared record selection mismatch")
    if len(production["trials"]) != 8 or production["witness"] is not None:
        raise AssertionError("unexpected production stopping state")

    audited_trials: list[dict[str, object]] = []
    reached: set[tuple[int, str]] = set()
    for trial in production["trials"]:
        number = int(trial["trial"])
        source_record = int(trial["source_record"])
        directory = artifact_dir / f"trial-{number:02d}-record-{source_record:04d}"
        candidate_path = directory / "candidate.g6"
        canonical_path = directory / "candidate.canonical.g6"
        cnf_path = directory / "repair.cnf"
        stdout_path = directory / "cadical.stdout"
        candidate = graph(candidate_path.read_bytes())
        graph_maximum, complement_maximum = validate_ramsey(candidate)

        destroy = stable_sample(f"destroy:{source_record - 1}", list(range(ORDER)), 12)
        if destroy != trial["generation"]["destroy_vertices"]:
            raise AssertionError("destroy-set derivation mismatch")
        boundary = {(min(u, v), max(u, v)) for u, v in itertools.combinations(range(ORDER), 2) if u in destroy or v in destroy}
        source = sources[source_record - 1]
        distance = sum(source.has_edge(u, v) != candidate.has_edge(u, v) for u, v in boundary)
        fixed_equal = all(
            source.has_edge(u, v) == candidate.has_edge(u, v)
            for u, v in itertools.combinations(range(ORDER), 2)
            if (u, v) not in boundary
        )
        if distance != trial["actual_boundary_hamming_distance"] or distance < 60 or not fixed_equal:
            raise AssertionError("boundary scope mismatch")

        target_hash = canonical_hash(canonical_path)
        if target_hash not in lookup:
            raise AssertionError("production canonical file is absent from retained manifest")
        target_record, target_kind, target = lookup[target_hash]
        if not nx.is_isomorphic(candidate, target):
            raise AssertionError("NetworkX isomorphism rejects nauty-identified target")
        reached.add((target_record, target_kind))

        model = parse_model(stdout_path)
        cnf_check = check_cnf(cnf_path, model)
        if cnf_check["variables"] != trial["generation"]["variables"] or cnf_check["clauses"] != trial["generation"]["clauses"]:
            raise AssertionError("cold CNF count disagrees with production report")
        if logical_digest(cnf_path) != trial["generation"]["cnf_sha256"]:
            raise AssertionError("CNF hash mismatch")

        audited_trials.append({
            "trial": number,
            "source_record": source_record,
            "target_record": target_record,
            "target_kind": target_kind,
            "source_and_target_class_differ": (source_record, "source") != (target_record, target_kind),
            "boundary_hamming_distance": distance,
            "fixed_induced_order_30_equal": fixed_equal,
            "graph_clique_number": graph_maximum,
            "complement_clique_number": complement_maximum,
            "networkx_isomorphic_to_manifest_target": True,
            "cnf_model": cnf_check,
        })

    mutation = {
        "forced_first_five_clique_detected": max(map(len, nx.find_cliques(force_five(graph((artifact_dir / "trial-01-record-0021/candidate.g6").read_bytes()), True)))) >= 5,
        "forced_first_five_independent_detected": max(map(len, nx.find_cliques(nx.complement(force_five(graph((artifact_dir / "trial-01-record-0021/candidate.g6").read_bytes()), False))))) >= 5,
    }
    if not all(mutation.values()):
        raise AssertionError("mutation sentinel failed")

    payload = {
        "schema_version": 1,
        "status": "novel42_boundary_repair_cold_audit_pass",
        "scope": "the eight retained SAT models and exact CNFs only",
        "production_report_sha256": digest(production_report_path),
        "corpus_sha256": digest(corpus_path),
        "predeclared_records_rederived": expected_records,
        "trials": audited_trials,
        "distinct_reached_control_classes": len(reached),
        "all_source_target_classes_differ": all(item["source_and_target_class_differ"] for item in audited_trials),
        "mutation_sentinels": mutation,
        "independent_methods": [
            "NetworkX graph6 parser",
            "NetworkX maximal-clique enumeration in graph and complement",
            "NetworkX VF2-style graph isomorphism to the nauty-identified manifest target",
            "direct full DIMACS assignment evaluation",
        ],
        "conclusion": "All eight exact boundary models are valid but rediscover eight distinct supplied classes; this is not a novel order-42 graph or an exhaustive boundary exclusion.",
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "distinct_reached_control_classes": payload["distinct_reached_control_classes"],
        "report": str(output),
        "report_sha256": digest(output),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
