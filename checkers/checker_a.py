#!/usr/bin/env python3
"""Transparent R(5,5) checker: independent parser plus direct 5-subset scan."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def parse_matrix_collection(path: Path) -> list[tuple[str, list[list[bool]]]]:
    graphs: list[tuple[str, list[str]]] = []
    name: str | None = None
    rows: list[str] = []
    for number, raw in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("> "):
            if name is not None:
                graphs.append((name, rows))
            name = line[2:].strip()
            if not name or any(old_name == name for old_name, _ in graphs):
                raise ValueError(f"line {number}: missing or duplicate graph name")
            rows = []
        else:
            if name is None:
                raise ValueError(f"line {number}: matrix row before graph header")
            if not line or any(bit not in "01" for bit in line):
                raise ValueError(f"line {number}: matrix rows must contain only 0 and 1")
            rows.append(line)
    if name is not None:
        graphs.append((name, rows))
    if not graphs:
        raise ValueError("no named matrices found")

    parsed: list[tuple[str, list[list[bool]]]] = []
    for graph_name, text_rows in graphs:
        n = len(text_rows)
        if n < 1 or any(len(row) != n for row in text_rows):
            raise ValueError(f"{graph_name}: matrix must be nonempty and square")
        adjacency = [[bit == "1" for bit in row] for row in text_rows]
        for i in range(n):
            if adjacency[i][i]:
                raise ValueError(f"{graph_name}: loop at vertex {i}")
            for j in range(i):
                if adjacency[i][j] != adjacency[j][i]:
                    raise ValueError(f"{graph_name}: asymmetric entries {i},{j}")
        parsed.append((graph_name, adjacency))
    return parsed


def decode_graph6_line(line: str, record: int) -> list[list[bool]]:
    if not line or any(ord(ch) < 63 or ord(ch) > 126 for ch in line):
        raise ValueError(f"record {record}: invalid graph6 character")
    values = [ord(ch) - 63 for ch in line]
    if values[0] == 63:
        raise ValueError(f"record {record}: only short graph6 n<=62 is supported")
    n = values[0]
    needed = (n * (n - 1) // 2 + 5) // 6
    if len(values) != 1 + needed:
        raise ValueError(
            f"record {record}: expected {1 + needed} graph6 characters, got {len(values)}"
        )
    bits: list[int] = []
    for value in values[1:]:
        bits.extend((value >> shift) & 1 for shift in range(5, -1, -1))
    adjacency = [[False] * n for _ in range(n)]
    cursor = 0
    for high in range(1, n):
        for low in range(high):
            edge = bool(bits[cursor])
            cursor += 1
            adjacency[low][high] = edge
            adjacency[high][low] = edge
    if any(bits[cursor:]):
        raise ValueError(f"record {record}: nonzero graph6 padding bit")
    return adjacency


def parse_graph6(path: Path) -> list[tuple[str, list[list[bool]]]]:
    raw_lines = path.read_bytes().splitlines()
    if not raw_lines:
        raise ValueError("empty graph6 file")
    graphs: list[tuple[str, list[list[bool]]]] = []
    for record, raw in enumerate(raw_lines, 1):
        if not raw:
            raise ValueError(f"record {record}: blank graph6 record")
        try:
            line = raw.decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError(f"record {record}: non-ASCII graph6 byte") from error
        graphs.append((f"g6_{record:04d}", decode_graph6_line(line, record)))
    return graphs


def force_first_five(adjacency: list[list[bool]], value: bool) -> None:
    if len(adjacency) < 5:
        raise ValueError("force control needs at least 5 vertices")
    for i in range(5):
        for j in range(i):
            adjacency[i][j] = value
            adjacency[j][i] = value


def delete_vertex(adjacency: list[list[bool]], vertex: int) -> list[list[bool]]:
    n = len(adjacency)
    if vertex < 0 or vertex >= n:
        raise ValueError(f"delete vertex {vertex} outside 0..{n - 1}")
    keep = [v for v in range(n) if v != vertex]
    return [[adjacency[u][v] for v in keep] for u in keep]


def check(name: str, adjacency: list[list[bool]]) -> dict[str, object]:
    n = len(adjacency)
    zero: list[list[int]] = []
    one: list[list[int]] = []
    for vertices in itertools.combinations(range(n), 5):
        values = [adjacency[u][v] for offset, u in enumerate(vertices) for v in vertices[offset + 1 :]]
        if all(values):
            one.append(list(vertices))
        elif not any(values):
            zero.append(list(vertices))
    degrees = [sum(row) for row in adjacency]
    return {
        "id": name,
        "n": n,
        "edges": sum(degrees) // 2,
        "degrees": degrees,
        "zero_k5": zero,
        "one_k5": one,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("matrix", "graph6"), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--id")
    parser.add_argument("--force", choices=("clique", "independent"))
    parser.add_argument("--delete", type=int)
    args = parser.parse_args()
    if args.force is not None and args.delete is not None:
        parser.error("--force and --delete are mutually exclusive")

    graphs = parse_matrix_collection(args.input) if args.format == "matrix" else parse_graph6(args.input)
    if args.id is not None:
        graphs = [(name, graph) for name, graph in graphs if name == args.id]
        if len(graphs) != 1:
            raise ValueError(f"graph id {args.id!r} not found exactly once")
    results = []
    for name, original in graphs:
        adjacency = [row[:] for row in original]
        if args.force is not None:
            force_first_five(adjacency, args.force == "clique")
            name += f"_forced_{args.force}"
        if args.delete is not None:
            adjacency = delete_vertex(adjacency, args.delete)
            name += f"_deleted_{args.delete}"
        results.append(check(name, adjacency))
    print(json.dumps({"checker": "A-direct-combinations", "graphs": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

