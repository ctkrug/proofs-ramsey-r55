#!/usr/bin/env python3
"""Direct raw Springer-matrix parser and radius-1 R(5,5) checker.

This implementation deliberately does not import the older matrix or graph6
parsers.  It scans every 5-subset once and derives every one-edge-flip result
from the ten edge values on that subset.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path


ORDER = 43
TITLE = "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"


def parse_raw(path: Path) -> list[list[int]]:
    raw = path.read_bytes()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("publisher matrix is not ASCII") from error
    if not text.endswith("\n"):
        raise ValueError("publisher matrix lacks its final LF")
    lines = text.splitlines()
    if len(lines) != ORDER + 1:
        raise ValueError(f"publisher matrix must have one title and {ORDER} rows")
    if lines[0] != TITLE:
        raise ValueError("publisher title line mismatch")

    matrix: list[list[int]] = []
    for row_number, line in enumerate(lines[1:]):
        tokens = line.split(" ")
        if len(tokens) != ORDER or any(token not in {"0", "1"} for token in tokens):
            raise ValueError(f"row {row_number} is not exactly {ORDER} single-space-delimited bits")
        matrix.append([int(token) for token in tokens])
    for i in range(ORDER):
        if matrix[i][i] != 0:
            raise ValueError(f"nonzero diagonal at {i}")
        for j in range(i):
            if matrix[i][j] != matrix[j][i]:
                raise ValueError(f"asymmetry at {i},{j}")
    return matrix


def upper_triangle_bits(matrix: list[list[int]]) -> str:
    return "".join(str(matrix[low][high]) for high in range(1, len(matrix)) for low in range(high))


def direct_violations(matrix: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    zero: list[list[int]] = []
    one: list[list[int]] = []
    for vertices in itertools.combinations(range(len(matrix)), 5):
        values = [matrix[u][v] for u, v in itertools.combinations(vertices, 2)]
        if not any(values):
            zero.append(list(vertices))
        elif all(values):
            one.append(list(vertices))
    return zero, one


def radius1_delta_scan(matrix: list[list[int]]) -> list[dict[str, object]]:
    edges = [(u, v) for u in range(ORDER) for v in range(u + 1, ORDER)]
    index = {edge: position for position, edge in enumerate(edges)}
    seed_zero, seed_one = direct_violations(matrix)
    zero: list[list[list[int]]] = [[item[:] for item in seed_zero] for _ in edges]
    one: list[list[list[int]]] = [[item[:] for item in seed_one] for _ in edges]

    for vertices_tuple in itertools.combinations(range(ORDER), 5):
        vertices = list(vertices_tuple)
        subset_edges = list(itertools.combinations(vertices_tuple, 2))
        values = [matrix[u][v] for u, v in subset_edges]
        ones = sum(values)
        if ones == 0:
            for edge in subset_edges:
                zero[index[edge]].remove(vertices)
        elif ones == 1:
            edge = subset_edges[values.index(1)]
            zero[index[edge]].append(vertices)
        elif ones == 9:
            edge = subset_edges[values.index(0)]
            one[index[edge]].append(vertices)
        elif ones == 10:
            for edge in subset_edges:
                one[index[edge]].remove(vertices)

    for sets in zero + one:
        sets.sort()

    return [
        {
            "edge": [u, v],
            "original": matrix[u][v],
            "zero_k5": zero[position],
            "one_k5": one[position],
        }
        for position, (u, v) in enumerate(edges)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--seed-only", action="store_true")
    args = parser.parse_args()

    matrix = parse_raw(args.input)
    zero, one = direct_violations(matrix)
    bits = upper_triangle_bits(matrix)
    payload: dict[str, object] = {
        "checker": "A-direct-combinations-with-one-pass-flip-deltas",
        "source": {
            "n": ORDER,
            "edges": sum(sum(row) for row in matrix) // 2,
            "upper_triangle_bits": bits,
            "upper_triangle_sha256": hashlib.sha256(bits.encode("ascii")).hexdigest(),
        },
        "seed": {"zero_k5": zero, "one_k5": one},
    }
    if not args.seed_only:
        payload["radius1"] = radius1_delta_scan(matrix)
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
