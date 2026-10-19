# Kickoff gate proof (2026-10-19)

Four throwaway PRs against main, each branched from `claude/content-validators` with one
deliberate defect, plus a baseline PR with no defect. All closed unmerged, branches deleted.

| Defect | PR | Run (job that went red) | Result |
|---|---|---|---|
| Baseline, no defect | 4 | tests 39188798759, lint 39188798732 | all green |
| A test deleted so python runs 15 checks against floor 16 | 5 | tests 39188807910 | `test` red: `FAIL python: 15 checks, floor 16` (check_floors) |
| Floor lowered in `expected_checks.txt` only (python 70, main has 78); ratchet added in fix round 1 | 12 | tests 39189306699 (baseline PR 11: tests 39189298045 green) | `test` red at the floor ratchet step: `FAIL python: floor lowered to 70 (base has 78)` |
| Trainer `TESTOVER,Cap` with a level 30 Pokemon listed in segment gym1 (cap 14) | 6 | tests 39188818187 | `test` red: `test_real_repo_is_valid` and `SUITE content FAILED`, error "over cap 14" |
| Unregistered file `game/Graphics/unregistered_gate_test.png` | 7 | tests 39188826706 | `test` red: added file matches no Paths glob in the register |
| Planted `PSC_TEST_SECRET_` plus 16 characters in `docs/gate_secret_test.txt` | 8 | lint 39188835139 | `gitleaks` red: rule `psc-test-secret`, leaks found: 1 |

The floor ratchet (`check_floors.py --base`, fed by tests.yml from the base branch's floors) closes the gap found in the first round, where lowering the floor file itself turned nothing red. The first-round "count below floor" row stays as a second proof.
