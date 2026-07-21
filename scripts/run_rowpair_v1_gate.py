#!/usr/bin/env python3
"""Build the rowpair-v1 packet and the exact central-distance null certificate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path


EMIN = {
    1: 0, 2: 0, 3: 0, 4: 0, 5: 1, 6: 2, 7: 3, 8: 4,
    9: 6, 10: 8, 11: 10, 12: 12, 13: 17, 14: 22, 15: 27,
    16: 32, 17: 41, 18: 50, 19: 57, 20: 68, 21: 77,
    22: 88, 23: 101, 24: 116,
}
EMAX = {
    1: 0, 2: 1, 3: 3, 4: 5, 5: 8, 6: 12, 7: 16, 8: 21,
    9: 27, 10: 33, 11: 40, 12: 48, 13: 53, 14: 60, 15: 66,
    16: 72, 17: 79, 18: 85, 19: 92, 20: 100, 21: 107,
    22: 114, 23: 122, 24: 132,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def krawtchouk(n: int, k: int, h: int) -> int:
    return sum(
        (-1) ** i * math.comb(h, i) * math.comb(n - h, k - i)
        for i in range(max(0, k - (n - h)), min(k, h) + 1)
    )


def allowed_distances(n: int, a: int, b: int) -> dict[str, list[int]]:
    edge_lo, edge_hi = max(0, a + b - n), min(a - 1, b - 1, 13)
    non_lo = max(0, a + b - n + 2)
    non_hi = min(a, b, a + b - n + 15)
    edge = [a + b - 2 * c for c in range(edge_lo, edge_hi + 1)] if edge_lo <= edge_hi else []
    nonedge = [a + b - 2 * c for c in range(non_lo, non_hi + 1)] if non_lo <= non_hi else []
    return {
        "edge": sorted(edge),
        "nonedge": sorted(nonedge),
        "union": sorted(set(edge) | set(nonedge)),
    }


def profile_count(n: int) -> int:
    degrees = list(range(n - 25, 25))
    count = 0

    def visit(position: int, remaining: int, degree_sum: int) -> None:
        nonlocal count
        if position == len(degrees) - 1:
            if (degree_sum + remaining * degrees[position]) % 2 == 0:
                count += 1
            return
        degree = degrees[position]
        for multiplicity in range(remaining + 1):
            visit(position + 1, remaining - multiplicity,
                  degree_sum + multiplicity * degree)

    visit(0, n, 0)
    return count


def doubled_excess_interval(n: int, degree: int) -> tuple[int, int]:
    dual_order = n - 1 - degree
    lower = (
        2 * (math.comb(dual_order, 2) - EMAX[dual_order] - EMAX[degree])
        - degree * (n - 2 * degree)
    )
    upper = (
        2 * (math.comb(dual_order, 2) - EMIN[dual_order] - EMIN[degree])
        - degree * (n - 2 * degree)
    )
    return lower, upper


def parse_ledger(path: Path) -> list[dict]:
    lines = path.read_text(encoding="ascii").splitlines()
    if not lines or lines[0] != "rowpair-ledger-v1":
        raise ValueError("bad ledger header")
    graphs: list[dict] = []
    current = None
    for line in lines[1:]:
        fields = line.split("\t")
        if fields[0] == "G":
            current = {
                "index": int(fields[1]),
                "variant": fields[2],
                "degrees": tuple(map(int, fields[3].split(","))),
                "types": [],
            }
            graphs.append(current)
        elif fields[0] == "T" and current is not None:
            if (int(fields[1]), fields[2]) != (current["index"], current["variant"]):
                raise ValueError("type record attached to wrong graph")
            current["types"].append(tuple(map(int, fields[3:])))
        else:
            raise ValueError("malformed ledger")
    return graphs


def validate_control_graph(graph: dict) -> dict:
    degrees = graph["degrees"]
    n = len(degrees)
    histogram = Counter(degrees)
    origin_pairs = Counter()
    edge_origin = Counter()
    common_origin = Counter()
    common_via_edges = Counter()
    distance_counts = Counter({0: n})
    edge_c13 = nonedge_q13 = total = 0
    pair_distance_min, pair_distance_max = n + 1, -1
    for a, b, epsilon, common, common_non, distance, count in graph["types"]:
        if distance != a + b - 2 * common:
            raise ValueError("row-distance identity failure")
        if common_non != n - 2 - a - b + 2 * epsilon + common:
            raise ValueError("common-nonneighbour identity failure")
        support = allowed_distances(n, a, b)["edge" if epsilon else "nonedge"]
        if distance not in support:
            raise ValueError("pair outside exact colour support")
        if epsilon and common > 13:
            raise ValueError("edge with more than 13 common neighbours")
        if not epsilon and common_non > 13:
            raise ValueError("nonedge with more than 13 common nonneighbours")
        origin_pairs[a] += count
        common_origin[a] += common * count
        if epsilon:
            edge_origin[a] += count
            common_via_edges[a] += (b - 1) * count
            if common == 13:
                edge_c13 += count
        elif common_non == 13:
            nonedge_q13 += count
        distance_counts[distance] += count
        pair_distance_min = min(pair_distance_min, distance)
        pair_distance_max = max(pair_distance_max, distance)
        total += count
    if total != n * (n - 1):
        raise ValueError("wrong ordered-pair total")
    for degree, multiplicity in histogram.items():
        if origin_pairs[degree] != multiplicity * (n - 1):
            raise ValueError("degree-pair marginal failure")
        if edge_origin[degree] != degree * multiplicity:
            raise ValueError("edge-origin marginal failure")
        if common_origin[degree] != common_via_edges[degree]:
            raise ValueError("aggregate common-neighbour identity failure")
    kraw_values = []
    for k in range(n + 1):
        value = sum(count * krawtchouk(n, k, distance)
                    for distance, count in distance_counts.items())
        if value < 0:
            raise ValueError("Delsarte inequality failure on a control")
        kraw_values.append(value)
    return {
        "histogram": tuple(sorted(histogram.items())),
        "distance_min": pair_distance_min,
        "distance_max": pair_distance_max,
        "edge_c13": edge_c13,
        "nonedge_q13": nonedge_q13,
        "minimum_krawtchouk_sum": min(kraw_values),
    }


def check_complement_pair(original: dict, complement: dict) -> None:
    n = len(original["degrees"])
    mapped = Counter()
    for a, b, epsilon, common, common_non, distance, count in original["types"]:
        mapped[(n - 1 - a, n - 1 - b, 1 - epsilon, common_non, common,
                distance + 2 * (1 - 2 * epsilon))] += count
    actual = Counter()
    for *key, count in complement["types"]:
        actual[tuple(key)] += count
    if mapped != actual:
        raise ValueError("complement row-distance transformation failure")


def central_certificate(n: int) -> dict:
    degrees = list(range(n - 25, 25))
    even_distance = 22
    odd_distance = 21 if n == 43 else 23
    support_checks = []
    for a in degrees:
        for b in range(a, 25):
            distance = even_distance if (a + b) % 2 == 0 else odd_distance
            support = allowed_distances(n, a, b)
            if distance not in support["union"]:
                raise ValueError("central template is outside union support")
            support_checks.append({
                "a": a, "b": b, "distance": distance,
                "edge_allowed": distance in support["edge"],
                "nonedge_allowed": distance in support["nonedge"],
            })
    checks = []
    minimum = None
    zero_count = 0
    for even_vertices in range(n + 1):
        odd_vertices = n - even_vertices
        same_ordered = even_vertices * (even_vertices - 1) + odd_vertices * (odd_vertices - 1)
        cross_ordered = 2 * even_vertices * odd_vertices
        for k in range(n + 1):
            value = (
                n * krawtchouk(n, k, 0)
                + same_ordered * krawtchouk(n, k, even_distance)
                + cross_ordered * krawtchouk(n, k, odd_distance)
            )
            if value < 0:
                raise ValueError("central template violates a Delsarte inequality")
            minimum = value if minimum is None else min(minimum, value)
            zero_count += value == 0
            checks.append({"even_vertices": even_vertices, "k": k, "value": value})
    intervals = {str(d): list(doubled_excess_interval(n, d)) for d in degrees}
    if not all(lower < 0 < upper for lower, upper in intervals.values()):
        raise ValueError("unexpected scalar excess interval")
    return {
        "degree_range": [degrees[0], degrees[-1]],
        "profile_definition": {
            "multiplicities_sum": n,
            "handshake_degree_sum_even": True,
        },
        "profile_count": profile_count(n),
        "published_extremal_doubled_excess_intervals": intervals,
        "profiles_surviving_interval_test": profile_count(n),
        "central_even_sum_distance": even_distance,
        "central_odd_sum_distance": odd_distance,
        "support_checks": support_checks,
        "delsarte_checks": checks,
        "minimum_delsarte_sum": minimum,
        "zero_delsarte_sum_count": zero_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--python-ledger", type=Path, required=True)
    parser.add_argument("--c-ledger", type=Path, required=True)
    parser.add_argument("--c-checker", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", default=[])
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    subprocess.run([
        sys.executable, str(root / "scripts" / "rowpair_ledger_a.py"),
        str(args.corpus), str(args.python_ledger),
    ], check=True)
    subprocess.run([str(args.c_checker), str(args.corpus), str(args.c_ledger)], check=True)
    if args.python_ledger.read_bytes() != args.c_ledger.read_bytes():
        raise ValueError("Python and C control ledgers differ")

    graphs = parse_ledger(args.python_ledger)
    if len(graphs) != 656:
        raise ValueError(f"expected 656 supplied/complement controls, got {len(graphs)}")
    stats = []
    for graph in graphs:
        stats.append(validate_control_graph(graph))
    for offset in range(0, len(graphs), 2):
        check_complement_pair(graphs[offset], graphs[offset + 1])

    degree_histograms = {entry["histogram"] for entry in stats}
    report = {
        "schema": "rowpair-v1",
        "claim_scope": (
            "The uncoloured union-support adjacency-row Delsarte pair LP only; "
            "not the coloured edge/nonedge LP, not adjacency symmetry, and not R(5,5)."
        ),
        "corpus": {
            "path": str(args.corpus),
            "sha256": sha256(args.corpus),
            "records_in_source": 328,
            "controls_with_complements": len(graphs),
            "distinct_degree_histograms": len(degree_histograms),
            "row_distance_range": [
                min(entry["distance_min"] for entry in stats),
                max(entry["distance_max"] for entry in stats),
            ],
            "ordered_edge_pairs_with_13_common_neighbours": sum(entry["edge_c13"] for entry in stats),
            "ordered_nonedge_pairs_with_13_common_nonneighbours": sum(entry["nonedge_q13"] for entry in stats),
            "minimum_control_krawtchouk_sum": min(entry["minimum_krawtchouk_sum"] for entry in stats),
            "complement_transform_checked": True,
            "aggregate_common_neighbour_identity_checked": True,
        },
        "ledgers": {
            "python": {"path": str(args.python_ledger), "sha256": sha256(args.python_ledger)},
            "c": {"path": str(args.c_ledger), "sha256": sha256(args.c_ledger)},
            "byte_identical": True,
        },
        "published_baseline": {
            "extremal_table": {str(d): [EMIN[d], EMAX[d]] for d in sorted(EMIN)},
            "interpretation": (
                "For a degree-d vertex, bound the edge counts of its (4,5,d) neighbourhood "
                "and complementary (4,5,n-1-d) dual neighbourhood using the published extrema, "
                "then apply the doubled m=2 excess identity."
            ),
        },
        "orders": {str(n): central_certificate(n) for n in (43, 44, 45)},
        "conclusion": {
            "raw_profiles": sum(profile_count(n) for n in (43, 44, 45)),
            "profiles_cut_by_published_extremal_interval": 0,
            "profiles_cut_by_uncoloured_union_support_delsarte_pair_lp": 0,
            "reason": (
                "For each degree pair, put all off-diagonal mass at distance 22 for even "
                "weight sum and at distance 21 (n=43) or 23 (n=44,45) for odd weight sum. "
                "The stored exact integer checks prove support and every Krawtchouk inequality "
                "for every possible parity-class size."
            ),
        },
        "sources": [{"path": str(path), "sha256": sha256(path)} for path in args.source],
        "tools": {
            "python": sys.version.split()[0],
            "c_checker": str(args.c_checker),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "output": str(args.output),
        "output_sha256": sha256(args.output),
        "profiles": report["conclusion"]["raw_profiles"],
        "cuts": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
