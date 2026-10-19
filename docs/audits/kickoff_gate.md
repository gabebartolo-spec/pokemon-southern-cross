# Kickoff gate proof (2026-10-19)

Four throwaway PRs against main, each branched from `claude/content-validators` with one
deliberate defect, plus a baseline PR with no defect. All closed unmerged, branches deleted.

| Defect | PR | Run (job that went red) | Result |
|---|---|---|---|
| Baseline, no defect | 4 | tests 39188798759, lint 39188798732 | all green |
| A test deleted so python runs 15 checks against floor 16 | 5 | tests 39188807910 | `test` red: `FAIL python: 15 checks, floor 16` (check_floors) |
| Trainer `TESTOVER,Cap` with a level 30 Pokemon listed in segment gym1 (cap 14) | 6 | tests 39188818187 | `test` red: `test_real_repo_is_valid` and `SUITE content FAILED`, error "over cap 14" |
| Unregistered file `game/Graphics/unregistered_gate_test.png` | 7 | tests 39188826706 | `test` red: added file matches no Paths glob in the register |
| Planted `PSC_TEST_SECRET_` plus 16 characters in `docs/gate_secret_test.txt` | 8 | lint 39188835139 | `gitleaks` red: rule `psc-test-secret`, leaks found: 1 |

Gaps found: the floor file itself can be lowered without any check going red (the floor check
compares counts to the file, not to history). A ratchet against main's floors is not built.
