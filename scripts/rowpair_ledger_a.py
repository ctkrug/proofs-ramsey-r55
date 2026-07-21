#!/usr/bin/env python3
"""Independent Python adjacency-row ledger for the authenticated R(5,5,42) controls.

The output is deliberately a simple, canonical TSV so that a separately written C
implementation can be compared byte for byte.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path


def parse_graph6(line: bytes) -> list[int]:
    line = line.strip()
    if not line or line.startswith(b">>"):
        raise ValueError("expected one short graph6 record without a header")
    n = line[0] - 63
    if not 0 <= n <= 62:
        raise ValueError("only short graph6 records are accepted")
    need = (n * (n - 1) // 2 + 5) // 6
    if len(line) != 1 + need:
        raise ValueError(f"wrong graph6 length for order {n}: {len(line)}")
    rows = [0] * n
    bit_index = 0
    for j in range(1, n):
        for i in range(j):
            value = line[1 + bit_index // 6] - 63
            if not 0 <= value < 64:
                raise ValueError("invalid graph6 byte")
            if (value >> (5 - bit_index % 6)) & 1:
                rows[i] |= 1 << j
                rows[j] |= 1 << i
            bit_index += 1
    return rows


def complement(rows: list[int]) -> list[int]:
    mask = (1 << len(rows)) - 1
    return [(~row) & mask & ~(1 << i) for i, row in enumerate(rows)]


def graph_lines(index: int, variant: str, rows: list[int]) -> list[str]:
    n = len(rows)
    degrees = [row.bit_count() for row in rows]
    result = [f"G\t{index:03d}\t{variant}\t" + ",".join(map(str, degrees))]
    types: Counter[tuple[int, int, int, int, int, int]] = Counter()
    for u in range(n):
        for v in range(n):
            if u == v:
                continue
            epsilon = (rows[u] >> v) & 1
            common = (rows[u] & rows[v]).bit_count()
            distance = degrees[u] + degrees[v] - 2 * common
            common_non = n - 2 - degrees[u] - degrees[v] + 2 * epsilon + common
            types[(degrees[u], degrees[v], epsilon, common, common_non, distance)] += 1
    for key in sorted(types):
        result.append(
            "T\t{:03d}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                index, variant, *key, types[key]
            )
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    records = [line for line in args.input.read_bytes().splitlines() if line]
    output = ["rowpair-ledger-v1"]
    for index, record in enumerate(records):
        rows = parse_graph6(record)
        output.extend(graph_lines(index, "O", rows))
        output.extend(graph_lines(index, "C", complement(rows)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(output) + "\n", encoding="ascii")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
