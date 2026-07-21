#!/usr/bin/env python3
"""Exact radius-two evaluator using five-set contribution arithmetic.

The pair ledger is ordered by first listing edges as
``(0,1), (0,2), ..., (41,42)`` and then listing unordered pairs of
distinct edge indices lexicographically.  Unlike the C checker, this program
does not search for cliques separately for every edited graph.  It scans each
five-set once and records exactly which two-edge edits can make or unmake that
five-set monochromatic.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


ORDER = 43
EDGE_COUNT = ORDER * (ORDER - 1) // 2
PAIR_COUNT = EDGE_COUNT * (EDGE_COUNT - 1) // 2
TITLE = "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"


def parse_raw(path: Path) -> list[list[int]]:
    raw = path.read_bytes()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("publisher matrix is not ASCII") from error
    if not text.endswith("\n"):
        raise ValueError("publisher matrix lacks its final LF")
    rows = text.splitlines()
    if len(rows) != ORDER + 1 or rows[0] != TITLE:
        raise ValueError("publisher title or row count mismatch")
    matrix = []
    for row_number, row in enumerate(rows[1:]):
        tokens = row.split(" ")
        if len(tokens) != ORDER or any(token not in {"0", "1"} for token in tokens):
            raise ValueError(f"row {row_number} is not exactly 43 single-space-delimited bits")
        matrix.append([int(token) for token in tokens])
    for u in range(ORDER):
        if matrix[u][u] != 0:
            raise ValueError("matrix diagonal must be zero")
        for v in range(u + 1, ORDER):
            if matrix[u][v] != matrix[v][u]:
                raise ValueError("matrix must be symmetric")
    return matrix


def ordered_edges() -> list[tuple[int, int]]:
    return [(u, v) for u in range(ORDER) for v in range(u + 1, ORDER)]


def pair_offset(first: int) -> int:
    return first * (2 * EDGE_COUNT - first - 1) // 2


def pair_index(first: int, second: int) -> int:
    if first == second:
        raise ValueError("a radius-two edit must use two distinct edges")
    if first > second:
        first, second = second, first
    return pair_offset(first) + second - first - 1


def direct_violations(
    matrix: list[list[int]],
    selected: tuple[int, int] | None = None,
) -> tuple[list[list[int]], list[list[int]]]:
    edges = ordered_edges()
    toggled = set() if selected is None else {edges[selected[0]], edges[selected[1]]}
    zero_k5: list[list[int]] = []
    one_k5: list[list[int]] = []
    for vertices in itertools.combinations(range(ORDER), 5):
        values = []
        for u, v in itertools.combinations(vertices, 2):
            value = matrix[u][v]
            if (u, v) in toggled:
                value ^= 1
            values.append(value)
        if all(value == 0 for value in values):
            zero_k5.append(list(vertices))
        elif all(value == 1 for value in values):
            one_k5.append(list(vertices))
    return zero_k5, one_k5


def minimizer_record(
    matrix: list[list[int]],
    edge_pair: tuple[int, int],
) -> dict[str, object]:
    edges = ordered_edges()
    zero_k5, one_k5 = direct_violations(matrix, edge_pair)
    return {
        "edge_indices": list(edge_pair),
        "edges": [list(edges[edge_pair[0]]), list(edges[edge_pair[1]])],
        "zero_k5": zero_k5,
        "one_k5": one_k5,
        "total_burden": len(zero_k5) + len(one_k5),
    }


def all_pair_scores(matrix: list[list[int]]) -> tuple[list[int], list[list[int]], list[list[int]]]:
    edges = ordered_edges()
    edge_to_index = {edge: index for index, edge in enumerate(edges)}
    seed_zero, seed_one = direct_violations(matrix)
    scores = [len(seed_zero) + len(seed_one)] * PAIR_COUNT

    def adjust(first: int, second: int, delta: int) -> None:
        scores[pair_index(first, second)] += delta

    for vertices in itertools.combinations(range(ORDER), 5):
        subset_edges = list(itertools.combinations(vertices, 2))
        subset_indices = [edge_to_index[edge] for edge in subset_edges]
        subset_index_set = set(subset_indices)
        ones = [index for index, edge in zip(subset_indices, subset_edges) if matrix[edge[0]][edge[1]]]
        one_index_set = set(ones)
        zeros = [index for index in subset_indices if index not in one_index_set]

        if len(ones) in (0, 10):
            # This is a seed violation.  It ceases to be monochromatic iff at
            # least one of the selected edit edges lies inside the five-set.
            for first, second in itertools.combinations(subset_indices, 2):
                adjust(first, second, -1)
            for first in subset_indices:
                for second in range(EDGE_COUNT):
                    if second not in subset_index_set:
                        adjust(first, second, -1)
        elif len(ones) == 1:
            # Flip the sole 1 to 0 while the other edit stays outside.
            first = ones[0]
            for second in range(EDGE_COUNT):
                if second not in subset_index_set:
                    adjust(first, second, 1)
        elif len(ones) == 2:
            # Flip both 1s to obtain an all-zero K5.
            adjust(ones[0], ones[1], 1)
        elif len(ones) == 8:
            # Flip both 0s to obtain an all-one K5.
            adjust(zeros[0], zeros[1], 1)
        elif len(ones) == 9:
            # Flip the sole 0 to 1 while the other edit stays outside.
            first = zeros[0]
            for second in range(EDGE_COUNT):
                if second not in subset_index_set:
                    adjust(first, second, 1)

    if any(score < 0 for score in scores):
        raise AssertionError("negative burden exposes an invalid contribution update")
    return scores, seed_zero, seed_one


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--pair-indices", nargs=2, type=int, metavar=("FIRST", "SECOND"))
    args = parser.parse_args()
    matrix = parse_raw(args.matrix)

    if args.pair_indices is not None:
        first, second = args.pair_indices
        if not (0 <= first < EDGE_COUNT and 0 <= second < EDGE_COUNT and first != second):
            raise ValueError("pair indices must be distinct values in [0, 902]")
        pair = tuple(sorted((first, second)))
        print(json.dumps({"checker": "python-five-set-contributions", **minimizer_record(matrix, pair)}))
        return 0

    scores, seed_zero, seed_one = all_pair_scores(matrix)
    minimum = min(scores)
    minimizer_pairs = []
    cursor = 0
    for first in range(EDGE_COUNT):
        for second in range(first + 1, EDGE_COUNT):
            if scores[cursor] == minimum:
                minimizer_pairs.append((first, second))
            cursor += 1
    if cursor != PAIR_COUNT:
        raise AssertionError("pair-ledger cardinality mismatch")

    result = {
        "checker": "python-five-set-contributions",
        "order": ORDER,
        "seed_edges": sum(matrix[u][v] for u in range(ORDER) for v in range(u + 1, ORDER)),
        "seed_zero_k5": seed_zero,
        "seed_one_k5": seed_one,
        "edge_order": "(u,v) lexicographic for 0 <= u < v < 43",
        "pair_order": "(first_edge_index,second_edge_index) lexicographic with first < second",
        "pair_count": PAIR_COUNT,
        "minimum": minimum,
        "scores": scores,
        "minimizers": [minimizer_record(matrix, pair) for pair in minimizer_pairs],
    }
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
