---
name: psc-essentials-tests
description: Running and extending the Pokemon Southern Cross automated checks - tools/run_tests.sh suites (python, ruby, content), the SUITE lines, check floors in tests/expected_checks.txt, doc-size caps, and what CI does and does not cover. Extends the general game-architecture skill (~/.claude/skills). Use it before adding a test, a suite or a floor, when CI goes red on tests, or when deciding how to prove a change.
---

# Tests and check floors

The general rules are the `game-architecture` skill; this holds what is specific to this repo.

## Running

```bash
bash tools/run_tests.sh            # all suites
bash tools/run_tests.sh python     # or: ruby | content
```

Each passing suite prints `SUITE <name> CHECKS <n>`. A suite that cannot run here prints
`SUITE <name> SKIPPED` and exits 0: `ruby` when Ruby is not installed, `content` until
`tools/validate/content.py` exists. CI sets `PSC_CI=1`, which turns a missing runtime into a
failure, so a skip never hides in CI.

- `python`: `python -m pytest tests/python` (needs `pip install pytest`).
- `ruby`: minitest files `tests/ruby/test_*.rb`, loaded by `run_tests.sh`; runs in CI on any machine without Ruby.
- `content`: `tools/validate/content.py`, validating PBS and `content/`. It must print a line containing `CHECKS <n>`.

## Floors

`tests/expected_checks.txt` holds `<suite> <floor>` lines. `python tools/check_floors.py run.log`
exits 1 if a suite ran fewer checks than its floor, or a floored suite left no result (SKIPPED
is ignored). Raise the floor in the PR that adds checks to a suite; never lower one. To add a
suite: add a `suite_<name>` function and a case line in `tools/run_tests.sh`, then a floor line.

## Doc caps

`python tools/check_doc_sizes.py` (CI job `doc-caps`) fails if CLAUDE.md, docs/STATUS.md,
docs/DECISIONS.md or docs/ROADMAP.md is longer than its cap: the integer on its `Cap: N lines`
line. CLAUDE.md has no Cap line, so its cap is 120 lines, set inside the script.

## What CI does not cover

Essentials itself (Ruby on mkxp-z) is not run in CI. In-game behaviour is proven by playtest
captures in the PR body, not by CI. CI covers the tools, the content validators and the
Ruby units that do not need the engine.

## Learnings

`references/learnings.md`; add only what proved effective, with evidence.
