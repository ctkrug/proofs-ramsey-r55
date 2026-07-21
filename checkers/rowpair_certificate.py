#!/usr/bin/env python3
"""Cold exact checker for rowpair-v1, independent of the producing script."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


EXPECTED_EXTREMA = {
    1: (0, 0), 2: (0, 1), 3: (0, 3), 4: (0, 5), 5: (1, 8),
    6: (2, 12), 7: (3, 16), 8: (4, 21), 9: (6, 27), 10: (8, 33),
    11: (10, 40), 12: (12, 48), 13: (17, 53), 14: (22, 60),
    15: (27, 66), 16: (32, 72), 17: (41, 79), 18: (50, 85),
    19: (57, 92), 20: (68, 100), 21: (77, 107), 22: (88, 114),
    23: (101, 122), 24: (116, 132),
}


class Rejected(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def kraw_series(n: int, h: int) -> list[int]:
    if n == 0:
        return [1]
    values = [1, n - 2 * h]
    for k in range(1, n):
        numerator = (n - 2 * h) * values[k] - (n - k + 1) * values[k - 1]
        if numerator % (k + 1):
            raise Rejected("nonintegral Krawtchouk recurrence")
        values.append(numerator // (k + 1))
    return values


def direct_support(n: int, a: int, b: int, epsilon: int) -> set[int]:
    result = set()
    for common in range(n + 1):
        if epsilon:
            valid = (
                common >= a + b - n
                and common <= a - 1
                and common <= b - 1
                and common <= 13
            )
        else:
            common_non = n - 2 - a - b + 2 * epsilon + common
            valid = (
                common >= 0 and common <= a and common <= b
                and common_non >= 0 and common_non <= 13
            )
        if valid:
            result.add(a + b - 2 * common)
    return result


def profile_count_dp(n: int) -> int:
    states = {(0, 0): 1}
    for degree in range(n - 25, 25):
        following = defaultdict(int)
        for (used, parity), count in states.items():
            for multiplicity in range(n - used + 1):
                following[(used + multiplicity,
                           (parity + multiplicity * degree) & 1)] += count
        states = following
    return states[(n, 0)]


def expected_interval(n: int, degree: int) -> tuple[int, int]:
    dual = n - 1 - degree
    emin_d, emax_d = EXPECTED_EXTREMA[degree]
    emin_r, emax_r = EXPECTED_EXTREMA[dual]
    return (
        2 * (math.comb(dual, 2) - emax_r - emax_d) - degree * (n - 2 * degree),
        2 * (math.comb(dual, 2) - emin_r - emin_d) - degree * (n - 2 * degree),
    )


def parse_and_validate_ledger(data: bytes) -> dict:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise Rejected("ledger is not ASCII") from exc
    if not lines or lines[0] != "rowpair-ledger-v1":
        raise Rejected("bad ledger header")
    graphs = []
    current = None
    for line in lines[1:]:
        fields = line.split("\t")
        if fields[0] == "G" and len(fields) == 4:
            current = {
                "index": int(fields[1]), "variant": fields[2],
                "degrees": tuple(map(int, fields[3].split(","))), "types": [],
            }
            graphs.append(current)
        elif fields[0] == "T" and len(fields) == 10 and current is not None:
            if (int(fields[1]), fields[2]) != (current["index"], current["variant"]):
                raise Rejected("ledger grouping mismatch")
            current["types"].append(tuple(map(int, fields[3:])))
        else:
            raise Rejected("malformed ledger line")
    if len(graphs) != 656:
        raise Rejected("wrong number of controls")

    histograms = set()
    edge13 = nonedge13 = 0
    distance_min, distance_max = 10**9, -1
    minimum_kraw = None
    for graph in graphs:
        degrees = graph["degrees"]
        if len(degrees) != 42:
            raise Rejected("wrong control order")
        histogram = Counter(degrees)
        histograms.add(tuple(sorted(histogram.items())))
        pair_origins = Counter()
        edge_origins = Counter()
        left_common = Counter()
        right_common = Counter()
        distance_counts = Counter({0: 42})
        total = 0
        for a, b, epsilon, common, common_non, distance, count in graph["types"]:
            if count <= 0:
                raise Rejected("nonpositive ledger count")
            if distance != a + b - 2 * common:
                raise Rejected("distance identity failure")
            if common_non != 40 - a - b + 2 * epsilon + common:
                raise Rejected("common-nonneighbour identity failure")
            if distance not in direct_support(42, a, b, epsilon):
                raise Rejected("colour-support failure")
            pair_origins[a] += count
            left_common[a] += common * count
            if epsilon:
                edge_origins[a] += count
                right_common[a] += (b - 1) * count
                edge13 += count * (common == 13)
            else:
                nonedge13 += count * (common_non == 13)
            distance_counts[distance] += count
            distance_min = min(distance_min, distance)
            distance_max = max(distance_max, distance)
            total += count
        if total != 42 * 41:
            raise Rejected("pair total failure")
        for degree, multiplicity in histogram.items():
            if pair_origins[degree] != 41 * multiplicity:
                raise Rejected("pair marginal failure")
            if edge_origins[degree] != degree * multiplicity:
                raise Rejected("edge marginal failure")
            if left_common[degree] != right_common[degree]:
                raise Rejected("common-neighbour aggregate failure")
        series = {h: kraw_series(42, h) for h in distance_counts}
        for k in range(43):
            value = sum(count * series[h][k] for h, count in distance_counts.items())
            if value < 0:
                raise Rejected("control Delsarte failure")
            minimum_kraw = value if minimum_kraw is None else min(minimum_kraw, value)
    return {
        "graphs": len(graphs), "histograms": len(histograms),
        "edge13": edge13, "nonedge13": nonedge13,
        "distance_range": [distance_min, distance_max], "minimum_kraw": minimum_kraw,
    }


def validate_report(report: dict) -> None:
    if report.get("schema") != "rowpair-v1":
        raise Rejected("wrong report schema")
    table = {int(k): tuple(v) for k, v in report["published_baseline"]["extremal_table"].items()}
    if table != EXPECTED_EXTREMA:
        raise Rejected("published extremal table changed")
    total_profiles = 0
    for n in (43, 44, 45):
        item = report["orders"][str(n)]
        degrees = list(range(n - 25, 25))
        even_h, odd_h = 22, (21 if n == 43 else 23)
        if item["degree_range"] != [degrees[0], 24]:
            raise Rejected("wrong degree range")
        count = profile_count_dp(n)
        if item["profile_count"] != count or item["profiles_surviving_interval_test"] != count:
            raise Rejected("profile count mismatch")
        total_profiles += count
        intervals = {int(k): tuple(v) for k, v in item["published_extremal_doubled_excess_intervals"].items()}
        for degree in degrees:
            if intervals.get(degree) != expected_interval(n, degree):
                raise Rejected("excess interval mismatch")
            if not intervals[degree][0] < 0 < intervals[degree][1]:
                raise Rejected("claimed all-profile interval survival is unjustified")
        expected_support = []
        for a in degrees:
            for b in range(a, 25):
                h = even_h if (a + b) % 2 == 0 else odd_h
                edge = direct_support(n, a, b, 1)
                nonedge = direct_support(n, a, b, 0)
                if h not in edge | nonedge:
                    raise Rejected("central distance lacks support")
                expected_support.append({
                    "a": a, "b": b, "distance": h,
                    "edge_allowed": h in edge, "nonedge_allowed": h in nonedge,
                })
        if item["support_checks"] != expected_support:
            raise Rejected("support certificate mismatch")
        expected_checks = []
        minimum = None
        zeros = 0
        series0 = kraw_series(n, 0)
        series_even = kraw_series(n, even_h)
        series_odd = kraw_series(n, odd_h)
        for even_vertices in range(n + 1):
            odd_vertices = n - even_vertices
            same = even_vertices * (even_vertices - 1) + odd_vertices * (odd_vertices - 1)
            cross = 2 * even_vertices * odd_vertices
            for k in range(n + 1):
                value = n * series0[k] + same * series_even[k] + cross * series_odd[k]
                if value < 0:
                    raise Rejected("negative central Delsarte sum")
                minimum = value if minimum is None else min(minimum, value)
                zeros += value == 0
                expected_checks.append({"even_vertices": even_vertices, "k": k, "value": value})
        if item["delsarte_checks"] != expected_checks:
            raise Rejected("Delsarte certificate mismatch")
        if item["minimum_delsarte_sum"] != minimum or item["zero_delsarte_sum_count"] != zeros:
            raise Rejected("Delsarte summary mismatch")
    conclusion = report["conclusion"]
    if conclusion["raw_profiles"] != total_profiles:
        raise Rejected("total profile count mismatch")
    if conclusion["profiles_cut_by_published_extremal_interval"] != 0:
        raise Rejected("unexpected scalar cut count")
    if conclusion["profiles_cut_by_uncoloured_union_support_delsarte_pair_lp"] != 0:
        raise Rejected("unexpected Delsarte cut count")


def exhaustive_small_graph_control() -> int:
    checked = 0
    for n in range(1, 7):
        pairs = [(i, j) for j in range(1, n) for i in range(j)]
        for mask in range(1 << len(pairs)):
            rows = [0] * n
            for bit, (i, j) in enumerate(pairs):
                if (mask >> bit) & 1:
                    rows[i] |= 1 << j
                    rows[j] |= 1 << i
            degrees = [row.bit_count() for row in rows]
            comp_mask = (1 << n) - 1
            complements = [(~row) & comp_mask & ~(1 << i) for i, row in enumerate(rows)]
            distances = Counter()
            for u in range(n):
                for v in range(n):
                    direct = (rows[u] ^ rows[v]).bit_count()
                    common = (rows[u] & rows[v]).bit_count()
                    if direct != degrees[u] + degrees[v] - 2 * common:
                        raise Rejected("small-graph row identity failure")
                    distances[direct] += 1
                    if u != v:
                        epsilon = (rows[u] >> v) & 1
                        complement_distance = (complements[u] ^ complements[v]).bit_count()
                        if complement_distance != direct + 2 * (1 - 2 * epsilon):
                            raise Rejected("small-graph complement distance failure")
            series = {h: kraw_series(n, h) for h in distances}
            for k in range(n + 1):
                if sum(count * series[h][k] for h, count in distances.items()) < 0:
                    raise Rejected("small-graph Delsarte failure")
            checked += 1
    return checked


def require_rejection(report: dict, mutation) -> None:
    altered = copy.deepcopy(report)
    mutation(altered)
    try:
        validate_report(altered)
    except (Rejected, KeyError, TypeError, ValueError):
        return
    raise Rejected("certificate mutation was accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--python-ledger", type=Path, required=True)
    parser.add_argument("--c-ledger", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report_bytes = args.report.read_bytes()
    report = json.loads(report_bytes)
    validate_report(report)
    python_bytes, c_bytes = args.python_ledger.read_bytes(), args.c_ledger.read_bytes()
    if python_bytes != c_bytes:
        raise Rejected("the two retained ledgers differ")
    if sha256_bytes(python_bytes) != report["ledgers"]["python"]["sha256"]:
        raise Rejected("Python ledger hash mismatch")
    if sha256_bytes(c_bytes) != report["ledgers"]["c"]["sha256"]:
        raise Rejected("C ledger hash mismatch")
    ledger_stats = parse_and_validate_ledger(python_bytes)
    corpus_bytes = args.corpus.read_bytes()
    if sha256_bytes(corpus_bytes) != report["corpus"]["sha256"]:
        raise Rejected("corpus hash mismatch")
    if ledger_stats != {
        "graphs": 656,
        "histograms": report["corpus"]["distinct_degree_histograms"],
        "edge13": report["corpus"]["ordered_edge_pairs_with_13_common_neighbours"],
        "nonedge13": report["corpus"]["ordered_nonedge_pairs_with_13_common_nonneighbours"],
        "distance_range": report["corpus"]["row_distance_range"],
        "minimum_kraw": report["corpus"]["minimum_control_krawtchouk_sum"],
    }:
        raise Rejected("ledger summary mismatch")
    for source in report["sources"]:
        path = Path(source["path"])
        if not path.is_file() or sha256_bytes(path.read_bytes()) != source["sha256"]:
            raise Rejected("source artifact mismatch")

    small_graphs = exhaustive_small_graph_control()
    mutations = []
    require_rejection(report, lambda value: value["orders"]["43"]["support_checks"][0].__setitem__("distance", 24))
    mutations.append("central-distance")
    require_rejection(report, lambda value: value["orders"]["44"]["delsarte_checks"][0].__setitem__("value", 1))
    mutations.append("certificate-coefficient")
    require_rejection(report, lambda value: value["orders"]["45"].__setitem__("profile_count", 0))
    mutations.append("profile-count")
    altered_ledger = python_bytes.replace(b"\t1\n", b"\t2\n", 1)
    try:
        parse_and_validate_ledger(altered_ledger)
    except Rejected:
        mutations.append("ledger-count")
    else:
        raise Rejected("ledger-count mutation was accepted")
    altered_degree = python_bytes.replace(b"G\t000\tO\t19", b"G\t000\tO\t18", 1)
    try:
        parse_and_validate_ledger(altered_degree)
    except Rejected:
        mutations.append("degree-label")
    else:
        raise Rejected("degree-label mutation was accepted")
    if not ledger_stats["edge13"] or not ledger_stats["nonedge13"]:
        raise Rejected("the <=12 sharpness mutation would not be detected")
    mutations.append("common-bound-12")
    if not corpus_bytes:
        raise Rejected("empty corpus")
    tampered = bytearray(corpus_bytes)
    tampered[1] ^= 1
    if sha256_bytes(tampered) == report["corpus"]["sha256"]:
        raise Rejected("corpus-bit mutation was accepted")
    mutations.append("corpus-bit")

    audit = {
        "schema": "rowpair-v1-cold-audit",
        "status": "PASS",
        "report_sha256": sha256_bytes(report_bytes),
        "ledger_sha256": sha256_bytes(python_bytes),
        "ledger_stats": ledger_stats,
        "labelled_graphs_through_order_6": small_graphs,
        "rejected_mutations": mutations,
        "krawtchouk_implementation": "three-term integer recurrence",
        "profile_counter": "dynamic programming over multiplicities and handshake parity",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
