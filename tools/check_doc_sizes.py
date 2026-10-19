#!/usr/bin/env python3
"""Fail if a must-read doc is longer than its cap.

A doc's cap is the integer on its `Cap: N lines` line (the line must start with `Cap:`). CLAUDE.md has no Cap line, so its cap
is CLAUDE_MD_CAP below. A doc that exists but has no cap fails; a doc that does not exist yet
is skipped.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD_CAP = 120
DOCS = ["CLAUDE.md", "docs/STATUS.md", "docs/DECISIONS.md", "docs/ROADMAP.md"]


def main():
    failed = False
    for rel in DOCS:
        p = ROOT / rel
        if not p.exists():
            print(f"skip {rel}: not found")
            continue
        text = p.read_text(encoding="utf-8")
        n = len(text.splitlines())
        m = re.search(r"^Cap:\s*(\d+)\s*lines", text, re.M)
        cap = int(m.group(1)) if m else (CLAUDE_MD_CAP if rel == "CLAUDE.md" else None)
        if cap is None:
            print(f"FAIL {rel}: no `Cap: N lines` line")
            failed = True
        elif n > cap:
            print(f"FAIL {rel}: {n} lines, cap {cap}")
            failed = True
        else:
            print(f"ok   {rel}: {n} lines, cap {cap}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
