#!/usr/bin/env python3
"""Fail if a test function a suite defines never ran (this replaced the check floors).

Usage: functions_ran.py python <junit xml> [--tests <dir>]
       functions_ran.py ruby <minitest -v output> [--tests <dir>]

Every `test_*` function in the suite's files (tests/python/test_*.py: module level and in
`Test*` classes; tests/ruby/test_*.rb: every `def test_*`) must appear in the run's results.
A parametrised test counts once. Prints `SUITE <name> FUNCTIONS <ran> of <defined>`, then one
`never ran: <file>::<test>` line per function that did not run, and exits 1 if any is short.
Nothing to maintain by hand: a new test counts itself, so two PRs never edit the same line.
"""
import ast
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def defined_python(tests):
    """(file stem, name) for every test function pytest would collect."""
    names = Counter()
    for path in sorted(tests.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                names[(path.stem, node.name)] += 1
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                        names[(path.stem, f"{node.name}.{item.name}")] += 1
    return names


def ran_python(xml_path):
    """(file stem, name) for every test case in a pytest --junitxml report, params dropped."""
    names = set()
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        parts = case.get("classname", "").split(".")
        name = case.get("name", "").split("[", 1)[0]
        stem = next((p for p in parts if p.startswith("test_")), "")
        cls = parts[-1] if parts and parts[-1].startswith("Test") else ""
        names.add((stem, f"{cls}.{name}" if cls else name))
    return names


def defined_ruby(tests):
    names = Counter()
    for path in sorted(tests.glob("test_*.rb")):
        for m in re.finditer(r"^\s*def (test_\w+[?!]?)", path.read_text(encoding="utf-8"), re.M):
            names[(path.stem, m.group(1))] += 1
    return names


def ran_ruby(out_path):
    """Test names from minitest's verbose lines, `TestClass#test_name = 0.00 s = .`"""
    text = Path(out_path).read_text(encoding="utf-8", errors="replace")
    return Counter(m.group(1) for m in re.finditer(r"^\S+#(test_\w+[?!]?) = ", text, re.M))


def main(argv):
    args = argv[1:]
    tests = None
    if "--tests" in args:
        i = args.index("--tests")
        tests = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) != 2 or args[0] not in ("python", "ruby"):
        print(__doc__)
        return 2
    suite, result = args
    tests = tests or ROOT / "tests" / suite
    missing = []
    if suite == "python":
        defined = defined_python(tests)
        ran = ran_python(result)
        # A name defined twice in one file is shadowed: only the last one runs.
        missing = [key for key, n in defined.items() if key not in ran or n > 1]
    else:
        defined = defined_ruby(tests)
        ran = ran_ruby(result)
        left = Counter(ran)
        for (stem, name), n in sorted(defined.items()):
            for _ in range(n):
                if left[name] > 0:
                    left[name] -= 1
                else:
                    missing.append((stem, name))
    total = sum(defined.values())
    print(f"SUITE {suite} FUNCTIONS {total - len(missing)} of {total}")
    for stem, name in sorted(missing):
        print(f"never ran: {stem}::{name}")
    if total == 0:
        print(f"no test functions found in {tests}")
        return 1
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
