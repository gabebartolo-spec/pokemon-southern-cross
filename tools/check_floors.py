#!/usr/bin/env python3
"""Fail if any suite ran fewer checks than its floor in tests/expected_checks.txt.

Usage: check_floors.py <run log> [--floors <file>]

The log holds lines `SUITE <name> CHECKS <n>` (or `SUITE <name> SKIPPED`, which is ignored).
The floors file holds lines `<suite> <floor>`; `#` starts a comment. A suite with a floor but
no CHECKS line (and not SKIPPED) fails: a suite that silently did not run is a failure.
"""
import re
import sys
from pathlib import Path

DEFAULT_FLOORS = Path(__file__).resolve().parents[1] / "tests" / "expected_checks.txt"


def parse_floors(text):
    floors = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, floor = line.split()
        floors[name] = int(floor)
    return floors


def parse_log(text):
    counts, skipped = {}, set()
    for m in re.finditer(r"^SUITE (\S+) CHECKS (\d+)\s*$", text, re.M):
        counts[m.group(1)] = int(m.group(2))
    for m in re.finditer(r"^SUITE (\S+) SKIPPED\b", text, re.M):
        skipped.add(m.group(1))
    return counts, skipped


def main(argv):
    args = argv[1:]
    floors_path = DEFAULT_FLOORS
    if "--floors" in args:
        i = args.index("--floors")
        floors_path = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) != 1:
        print(__doc__)
        return 2
    floors = parse_floors(floors_path.read_text(encoding="utf-8"))
    counts, skipped = parse_log(Path(args[0]).read_text(encoding="utf-8", errors="replace"))
    failed = False
    for name, floor in sorted(floors.items()):
        if name in counts:
            ok = counts[name] >= floor
            print(f"{'ok  ' if ok else 'FAIL'} {name}: {counts[name]} checks, floor {floor}")
            failed |= not ok
        elif name in skipped:
            print(f"skip {name}: SKIPPED")
        else:
            print(f"FAIL {name}: no result in log, floor {floor}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
