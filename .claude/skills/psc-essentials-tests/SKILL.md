---
name: psc-essentials-tests
description: Running and extending the Pokemon Southern Cross automated checks - tools/run_tests.sh suites (python, ruby, content), the SUITE lines, the test-function count (tools/functions_ran.py), doc-size caps, and what CI does and does not cover. Extends the general game-architecture skill (~/.claude/skills). Use it before adding a test or a suite, when CI goes red on tests, or when deciding how to prove a change.
---

# Tests and the function count

The general rules are the `game-architecture` skill; this holds what is specific to this repo.

## Running

```bash
bash tools/run_tests.sh            # all suites
bash tools/run_tests.sh python     # or: ruby | content
```

Each passing suite prints `SUITE <name> CHECKS <n>`. A suite that cannot run here prints
`SUITE <name> SKIPPED` and exits 0: `ruby` when Ruby is not installed, `content` only if
`tools/validate/content.py` is missing. CI sets `PSC_CI=1`, which turns a missing runtime into a
failure, so a skip never hides in CI.

- `python`: `python -m pytest tests/python` (needs `pip install pytest`).
- `ruby`: minitest files `tests/ruby/test_*.rb`, loaded by `run_tests.sh`; runs in CI on any machine without Ruby.
- `content`: `tools/validate/content.py`, validating PBS and `content/`. It prints `CHECKS <n>`, n = number of validation rules (`len(content.RULES)`).

## Every test function ran (no floors)

The python and ruby suites print `SUITE <name> FUNCTIONS <ran> of <defined>`
(`tools/functions_ran.py`, called by `run_tests.sh`): every `test_*` function in the suite's
files must appear in the run's results (pytest's junit report, minitest's `-v` lines), and one
that never ran, or is shadowed by a second definition of the same name, fails the suite and is
named (`never ran: <file>::<test>`). A new test counts itself, so there is no floor file to edit
and two PRs never conflict over a count (director 2026-10-19, github-hygiene §4; this replaced
`tests/expected_checks.txt` and `check_floors.py`). To add a suite: add a `suite_<name>`
function and a case line in `tools/run_tests.sh`. Locally, run only the suite you touched.

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
