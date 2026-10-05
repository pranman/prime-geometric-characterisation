#!/usr/bin/env python3
"""Check the note's arithmetic and the actual LaTeX example table.

These finite checks supplement the proof; they do not prove the theorem.
Uses only the Python standard library. Run from any working directory.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import re
import sys


EXPECTED_TYPES = {
    1: [],
    2: [(2, 1)],
    3: [(3, 1)],
    4: [(2, 2), (4, 1)],
    5: [(5, 1)],
    6: [(2, 3), (3, 2), (6, 1)],
    7: [(7, 1)],
    8: [(2, 4), (4, 2), (8, 1)],
    9: [(3, 3), (9, 1)],
    10: [(2, 5), (5, 2), (10, 1)],
    11: [(11, 1)],
    12: [(2, 6), (3, 4), (4, 3), (6, 2), (12, 1)],
}

EXPECTED_CLASSES = {
    1: "neither prime nor composite", 2: "prime", 3: "prime", 4: "composite",
    5: "prime", 6: "composite", 7: "prime", 8: "composite",
    9: "composite", 10: "composite", 11: "prime", 12: "composite",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def representation_types(n: int) -> list[tuple[int, int]]:
    """Enumerate all permitted step counts directly, in increasing order."""
    return [(k, n // k) for k in range(2, n + 1) if n % k == 0]


def is_prime(n: int) -> bool:
    """Independent trial-division primality test."""
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def divisor_count(n: int) -> int:
    """Compute tau from prime exponents, independently of route enumeration."""
    remaining = n
    count = 1
    factor = 2
    while factor * factor <= remaining:
        exponent = 0
        while remaining % factor == 0:
            remaining //= factor
            exponent += 1
        count *= exponent + 1
        factor += 1
    if remaining > 1:
        count *= 2
    return count


def check_arithmetic(limit: int) -> None:
    polygon_only_exceptions = []
    for n in range(1, limit + 1):
        routes = representation_types(n)
        prime = is_prime(n)
        count = len(routes)
        require(count == divisor_count(n) - 1, f"Divisor count failed at N={n}")
        require((count == 0) == (n == 1), f"N=1 classification failed at N={n}")
        require((count == 1) == prime, f"Prime classification failed at N={n}")
        require((count >= 2) == (n >= 2 and not prime),
                f"Composite classification failed at N={n}")
        if n >= 2:
            unit_routes = [route for route in routes if route[1] == 1]
            require(unit_routes == [(n, 1)], f"Unit-step type failed at N={n}")
            require(prime == all(s == 1 for _, s in routes),
                    f"Unit-step theorem failed at N={n}")
            require(prime == (not any(s > 1 for _, s in routes)),
                    f"Non-unit witness criterion failed at N={n}")
            polygons = [route for route in routes if route[0] >= 3]
            if prime != all(s == 1 for _, s in polygons):
                polygon_only_exceptions.append(n)
        if n in EXPECTED_TYPES:
            require(routes == EXPECTED_TYPES[n], f"Example types failed at N={n}")
            classification = ("neither prime nor composite" if n == 1
                              else "prime" if prime else "composite")
            require(classification == EXPECTED_CLASSES[n],
                    f"Example classification failed at N={n}")

    require(representation_types(1) == [], "N=1 must have no representation")
    require(all(s == 1 for _, s in representation_types(1)) and not is_prime(1),
            "N=1 must illustrate why the universal criterion requires N>=2")
    require(polygon_only_exceptions == [4],
            f"Unexpected polygon-only exceptions: {polygon_only_exceptions}")
    require([route for route in representation_types(2) if route[0] >= 3] == [],
            "N=2 must have no polygon-only representation")


def parse_types(cell: str) -> list[tuple[int, int]]:
    pair_pattern = r"\(\s*(\d+)\s*,\s*(\d+)\s*\)"
    pairs = [(int(k), int(s)) for k, s in re.findall(pair_pattern, cell)]
    if not pairs:
        require(cell.strip().lower() in {"none", "---", r"\textemdash", "--"},
                f"Unrecognised empty representation cell: {cell!r}")
        return []
    residue = re.sub(pair_pattern, "", cell)
    for token in (r"\(", r"\)", r"\,", r"\;", r"\quad", "$", ","):
        residue = residue.replace(token, "")
    require(not residue.strip(), f"Unexpected representation text: {residue!r}")
    return pairs


def check_paper_table(paper: Path) -> None:
    source = paper.read_text(encoding="utf-8")
    start = "% BEGIN REPRESENTATION TABLE"
    end = "% END REPRESENTATION TABLE"
    require(source.count(start) == source.count(end) == 1,
            "The LaTeX source must contain exactly one pair of representation-table markers")
    require(source.index(start) < source.index(end), "Table markers are out of order")
    body = source.split(start, 1)[1].split(end, 1)[0]
    rows = {}
    row_pattern = r"\s*(\d+)\s*&\s*(.*?)\s*&\s*(.*?)\s*\\\\\s*"
    for raw_line in body.splitlines():
        line = raw_line.split("%", 1)[0].strip()
        if not re.match(r"\d", line):
            continue
        match = re.fullmatch(row_pattern, line)
        require(match is not None, f"Malformed example row: {raw_line!r}")
        n_text, types_cell, class_cell = match.groups()
        n = int(n_text)
        require(n not in rows, f"Duplicate example row for N={n}")
        classification = " ".join(class_cell.lower().split())
        require(classification in EXPECTED_CLASSES.values(),
                f"Invalid classification cell at N={n}: {class_cell!r}")
        rows[n] = (parse_types(types_cell), classification)
    expected = {n: (routes, EXPECTED_CLASSES[n]) for n, routes in EXPECTED_TYPES.items()}
    require(rows == expected, f"LaTeX example table differs from verified examples: {rows!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10_000,
                        help="largest positive integer checked (default: 10000; minimum: 12)")
    parser.add_argument("--paper", type=Path,
                        default=Path(__file__).resolve().parents[1] / "paper" /
                        "prime-geometric-characterisation.tex",
                        help="LaTeX source containing the example table")
    parser.add_argument("--arithmetic-only", action="store_true",
                        help="skip source-table validation while drafting")
    args = parser.parse_args()
    if args.limit < 12:
        parser.error("--limit must be at least 12 to include every published example")
    try:
        check_arithmetic(args.limit)
        print(f"PASS: arithmetic, classification and theorem for N=1..{args.limit:,}.")
        print("PASS: N=1 vacuity, N=2 existence, and polygon-only exception N=4.")
        print("PASS: all representation types and classifications for N=1..12.")
        if args.arithmetic_only:
            print("SKIP: LaTeX source-table validation (--arithmetic-only).")
        else:
            check_paper_table(args.paper)
            print("PASS: actual LaTeX example table matches all verified examples.")
    except (AssertionError, OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("Finite verification supplements, and does not replace, the proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
